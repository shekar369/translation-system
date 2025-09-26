#!/usr/bin/env python3
"""
Simple Translation System Testing Script
Uploads test documents and tests translations across key languages.
"""

import os
import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCS_DIR = "tests/test-documents"
RESULTS_DIR = "tests/translation-results"

# Test credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"

# Key languages to test
TEST_LANGUAGES = ['en', 'es', 'fr', 'de', 'ja']

def main():
    print("Starting Translation System Test")
    print("=" * 50)

    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)

    session = requests.Session()

    # Step 1: Register/Login
    print("Step 1: Authentication")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    # Try register (might fail if exists)
    register_response = session.post(f"{BASE_URL}/auth/register", json=register_data)

    # Login
    login_response = session.post(f"{BASE_URL}/auth/login", json=register_data)

    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        session.headers.update({'Authorization': f'Bearer {token}'})
        print("Authentication successful")
    else:
        print(f"Authentication failed: {login_response.status_code}")
        return

    # Step 2: Upload one test document (TXT for simplicity)
    print("\\nStep 2: Upload test document")
    test_file = "ai-future-tech.txt"
    file_path = os.path.join(TEST_DOCS_DIR, test_file)

    if not os.path.exists(file_path):
        print(f"Test file not found: {file_path}")
        return

    with open(file_path, 'rb') as f:
        files = {'file': (test_file, f)}
        upload_response = session.post(f"{BASE_URL}/api/documents/upload", files=files)

    if upload_response.status_code != 201:
        print(f"Upload failed: {upload_response.status_code}")
        return

    document_info = upload_response.json()
    document_id = document_info['id']
    print(f"Document uploaded successfully - ID: {document_id}")

    # Step 3: Create translation jobs
    print("\\nStep 3: Create translation jobs")
    jobs = []

    # Test English to other languages
    for target_lang in TEST_LANGUAGES:
        if target_lang != 'en':
            job_data = {
                "document_id": document_id,
                "source_language": "en",
                "target_language": target_lang
            }

            response = session.post(f"{BASE_URL}/api/translate/jobs", json=job_data)
            if response.status_code == 201:
                job_info = response.json()
                jobs.append((job_info['id'], 'en', target_lang))
                print(f"Job created: en -> {target_lang} (Job ID: {job_info['id']})")
            else:
                print(f"Failed to create job en -> {target_lang}: {response.status_code}")

    print(f"Created {len(jobs)} translation jobs")

    # Step 4: Process translation jobs
    print("\\nStep 4: Process translations")
    successful_jobs = []

    for job_id, source_lang, target_lang in jobs:
        print(f"Processing job {job_id}: {source_lang} -> {target_lang}")

        response = session.post(f"{BASE_URL}/api/translate/jobs/{job_id}/process")

        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'completed':
                print(f"Translation completed successfully")
                successful_jobs.append((job_id, source_lang, target_lang))
            elif result.get('status') == 'failed':
                print(f"Translation failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"Translation processing: {result.get('message', 'Processing...')}")
                successful_jobs.append((job_id, source_lang, target_lang))
        else:
            print(f"Processing failed: {response.status_code}")

        time.sleep(1)  # Small delay between processing

    # Step 5: Download translation results
    print("\\nStep 5: Download results")
    downloaded_files = []

    for job_id, source_lang, target_lang in successful_jobs:
        response = session.get(f"{BASE_URL}/api/translate/jobs/{job_id}/download")

        if response.status_code == 200:
            filename = f"translation_{source_lang}_to_{target_lang}_job_{job_id}.txt"
            filepath = os.path.join(RESULTS_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            downloaded_files.append(filename)
            print(f"Downloaded: {filename}")
        else:
            print(f"Download failed for job {job_id}: {response.status_code}")

    # Step 6: Summary
    print("\\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Document uploaded: {test_file}")
    print(f"Translation jobs created: {len(jobs)}")
    print(f"Successful translations: {len(successful_jobs)}")
    print(f"Files downloaded: {len(downloaded_files)}")

    if downloaded_files:
        print("\\nDownloaded files:")
        for filename in downloaded_files:
            print(f"  - {filename}")
        print(f"\\nResults saved to: {RESULTS_DIR}")

    print("\\nMANUAL EVALUATION STEPS:")
    print("1. Open files in results directory")
    print("2. Compare translations for accuracy")
    print("3. Check technical terminology preservation")
    print("4. Verify content completeness")

    print("\\nTest completed!")

if __name__ == "__main__":
    main()