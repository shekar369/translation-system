"""
Redis Streams Queue Service for job processing pipeline
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        # Redis configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.stream_prefix = os.getenv("QUEUE_STREAM_PREFIX", "jobs")

        # Initialize Redis client
        self.redis_client = None
        self._consumer_group = "translation-workers"
        self._consumer_name = f"worker-{os.getpid()}"

    async def _get_client(self):
        """Get or create Redis client"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client

    async def publish(self, stream_name: str, message: Dict[str, Any]) -> str:
        """Publish a message to a Redis stream"""
        try:
            client = await self._get_client()

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            # Convert message to string fields for Redis
            redis_message = {}
            for key, value in message.items():
                if isinstance(value, (dict, list)):
                    redis_message[key] = json.dumps(value)
                else:
                    redis_message[key] = str(value)

            # Add to stream
            stream_key = f"{self.stream_prefix}.{stream_name}"
            message_id = await client.xadd(stream_key, redis_message)

            logger.info(f"Published message to {stream_key}: {message_id}")
            return message_id

        except Exception as e:
            logger.error(f"Error publishing message to {stream_name}: {e}")
            raise

    async def consume(
        self,
        stream_name: str,
        handler: Callable[[Dict[str, Any]], None],
        batch_size: int = 10,
        block_ms: int = 1000
    ):
        """Consume messages from a Redis stream"""
        try:
            client = await self._get_client()
            stream_key = f"{self.stream_prefix}.{stream_name}"

            # Create consumer group if it doesn't exist
            try:
                await client.xgroup_create(
                    stream_key,
                    self._consumer_group,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group {self._consumer_group} for {stream_key}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            while True:
                try:
                    # Read messages from stream
                    messages = await client.xreadgroup(
                        self._consumer_group,
                        self._consumer_name,
                        {stream_key: ">"},
                        count=batch_size,
                        block=block_ms
                    )

                    for stream, msgs in messages:
                        for message_id, fields in msgs:
                            try:
                                # Parse message
                                parsed_message = {}
                                for key, value in fields.items():
                                    key = key.decode() if isinstance(key, bytes) else key
                                    value = value.decode() if isinstance(value, bytes) else value

                                    # Try to parse JSON fields
                                    try:
                                        parsed_message[key] = json.loads(value)
                                    except (json.JSONDecodeError, TypeError):
                                        parsed_message[key] = value

                                # Add metadata
                                parsed_message["_stream"] = stream.decode() if isinstance(stream, bytes) else stream
                                parsed_message["_message_id"] = message_id.decode() if isinstance(message_id, bytes) else message_id

                                # Process message
                                await handler(parsed_message)

                                # Acknowledge message
                                await client.xack(stream_key, self._consumer_group, message_id)
                                logger.debug(f"Processed and acknowledged message {message_id}")

                            except Exception as e:
                                logger.error(f"Error processing message {message_id}: {e}")
                                # Optionally move to dead letter queue here

                except redis.ConnectionError as e:
                    logger.error(f"Redis connection error: {e}")
                    await asyncio.sleep(5)  # Wait before retry
                except Exception as e:
                    logger.error(f"Error consuming from {stream_name}: {e}")
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Fatal error in consumer for {stream_name}: {e}")
            raise

    async def get_pending_messages(self, stream_name: str) -> List[Dict[str, Any]]:
        """Get pending messages for a consumer group"""
        try:
            client = await self._get_client()
            stream_key = f"{self.stream_prefix}.{stream_name}"

            pending = await client.xpending(
                stream_key,
                self._consumer_group
            )

            return {
                "count": pending["pending"],
                "min_id": pending["min"],
                "max_id": pending["max"],
                "consumers": pending["consumers"]
            }

        except Exception as e:
            logger.error(f"Error getting pending messages for {stream_name}: {e}")
            return {}

    async def claim_pending_messages(
        self,
        stream_name: str,
        min_idle_time_ms: int = 60000
    ) -> List[Dict[str, Any]]:
        """Claim pending messages that have been idle too long"""
        try:
            client = await self._get_client()
            stream_key = f"{self.stream_prefix}.{stream_name}"

            # Get pending messages
            pending_info = await client.xpending_range(
                stream_key,
                self._consumer_group,
                min="-",
                max="+",
                count=10
            )

            claimed_messages = []
            for msg_info in pending_info:
                message_id, consumer, idle_time, delivery_count = msg_info

                if idle_time >= min_idle_time_ms:
                    # Claim the message
                    claimed = await client.xclaim(
                        stream_key,
                        self._consumer_group,
                        self._consumer_name,
                        min_idle_time_ms,
                        [message_id]
                    )

                    if claimed:
                        claimed_messages.extend(claimed)

            return claimed_messages

        except Exception as e:
            logger.error(f"Error claiming pending messages for {stream_name}: {e}")
            return []

    async def delete_message(self, stream_name: str, message_id: str):
        """Delete a message from a stream"""
        try:
            client = await self._get_client()
            stream_key = f"{self.stream_prefix}.{stream_name}"

            result = await client.xdel(stream_key, message_id)
            logger.info(f"Deleted message {message_id} from {stream_key}")
            return result

        except Exception as e:
            logger.error(f"Error deleting message {message_id} from {stream_name}: {e}")
            return False

    async def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """Get information about a stream"""
        try:
            client = await self._get_client()
            stream_key = f"{self.stream_prefix}.{stream_name}"

            info = await client.xinfo_stream(stream_key)
            return {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
                "groups": info.get("groups", 0)
            }

        except Exception as e:
            logger.error(f"Error getting stream info for {stream_name}: {e}")
            return {}

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()

# Event types for the translation pipeline
class JobEvents:
    JOB_CREATED = "job.created"
    JOB_STARTED = "job.started"
    JOB_QUEUED = "job.queued"

    PARSING_STARTED = "job.parsing.started"
    PARSING_COMPLETED = "job.parsing.completed"
    PARSING_FAILED = "job.parsing.failed"

    TRANSCRIBING_STARTED = "job.transcribing.started"
    TRANSCRIBING_COMPLETED = "job.transcribing.completed"
    TRANSCRIBING_FAILED = "job.transcribing.failed"

    TRANSLATING_STARTED = "job.translating.started"
    TRANSLATING_COMPLETED = "job.translating.completed"
    TRANSLATING_FAILED = "job.translating.failed"

    POSTPROCESSING_STARTED = "job.postprocessing.started"
    POSTPROCESSING_COMPLETED = "job.postprocessing.completed"
    POSTPROCESSING_FAILED = "job.postprocessing.failed"

    REVIEW_REQUIRED = "job.review.required"
    REVIEW_COMPLETED = "job.review.completed"

    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"