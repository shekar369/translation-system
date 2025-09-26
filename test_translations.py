#!/usr/bin/env python3
"""
Comprehensive Translation System Testing Script
Uploads test documents and tests translations across all supported languages.
"""

import os
import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCS_DIR = "tests/test-documents"
RESULTS_DIR = "tests/translation-results"

# Test credentials - you may need to update these
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"

# Language combinations to test (subset for practical testing)
PRIORITY_LANGUAGES = ['en', 'es', 'fr', 'de', 'ja', 'zh']  # 6 languages = 30 combinations
ALL_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi']

class TranslationTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()

        # Create results directory
        os.makedirs(RESULTS_DIR, exist_ok=True)

    def authenticate(self):
        """Get authentication token"""
        print("[AUTH] Authenticating...")

        # Try to register first (might fail if user exists)
        register_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }

        register_response = self.session.post(f"{BASE_URL}/auth/register", json=register_data)
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        else:
            print("ℹ️  User already exists, proceeding with login")

        # Login
        login_response = self.session.post(f"{BASE_URL}/auth/login", json=register_data)

        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data['access_token']
            self.session.headers.update({'Authorization': f'Bearer {self.token}'})
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {login_response.status_code}")
            return False

    def get_supported_languages(self):
        """Get list of supported languages"""
        response = self.session.get(f"{BASE_URL}/api/translate/languages")
        if response.status_code == 200:
            return response.json()['languages']
        return {}

    def upload_document(self, file_path):
        """Upload a document and return document info"""
        print(f"📄 Uploading {os.path.basename(file_path)}...")

        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            response = self.session.post(f"{BASE_URL}/api/documents/upload", files=files)

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Uploaded successfully - ID: {data['id']}")
            return data
        else:
            print(f"❌ Upload failed: {response.status_code}")
            return None

    def create_translation_job(self, document_id, source_lang, target_lang):
        """Create a translation job"""
        job_data = {
            "document_id": document_id,
            "source_language": source_lang,
            "target_language": target_lang
        }

        response = self.session.post(f"{BASE_URL}/api/translate/jobs", json=job_data)

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Translation job created: {source_lang}→{target_lang} (Job ID: {data['id']})")
            return data
        else:
            print(f"❌ Job creation failed: {response.status_code}")
            return None

    def process_translation_job(self, job_id):
        """Process a translation job"""
        response = self.session.post(f"{BASE_URL}/api/translate/jobs/{job_id}/process")

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'completed':
                print(f"✅ Translation completed (Job {job_id})")
                return True
            elif data.get('status') == 'failed':
                print(f"❌ Translation failed (Job {job_id}): {data.get('error', 'Unknown error')}")
                return False
            else:
                print(f"ℹ️  Translation processing (Job {job_id}): {data.get('message', 'Processing...')}")
                return True
        else:
            print(f"❌ Processing failed for job {job_id}: {response.status_code}")
            return False

    def download_translation(self, job_id, filename_prefix):
        """Download translation result"""
        response = self.session.get(f"{BASE_URL}/api/translate/jobs/{job_id}/download")

        if response.status_code == 200:
            filename = f"{filename_prefix}_job_{job_id}.txt"
            filepath = os.path.join(RESULTS_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"✅ Downloaded: {filename}")
            return filepath
        else:
            print(f"❌ Download failed for job {job_id}: {response.status_code}")
            return None

    def get_translation_jobs(self):
        """Get all translation jobs"""
        response = self.session.get(f"{BASE_URL}/api/translate/jobs")
        if response.status_code == 200:
            return response.json()
        return []

    def run_comprehensive_test(self):
        """Run comprehensive translation testing"""
        print("🚀 Starting Comprehensive Translation Test")
        print("=" * 60)

        # Step 1: Authenticate
        if not self.authenticate():
            return

        # Step 2: Get supported languages
        languages = self.get_supported_languages()
        print(f"📋 Found {len(languages)} supported languages: {list(languages.keys())}")

        # Step 3: Upload all test documents
        print("\n📁 UPLOADING TEST DOCUMENTS")
        print("-" * 30)

        uploaded_docs = []
        test_files = [
            "ai-future-tech.txt",
            "ai-future-tech.html",
            "ai-future-tech.rtf",
            "ai-future-tech.pdf",
            "ai-future-tech.docx"
        ]

        for filename in test_files:
            filepath = os.path.join(TEST_DOCS_DIR, filename)
            if os.path.exists(filepath):
                doc_info = self.upload_document(filepath)
                if doc_info:
                    uploaded_docs.append((doc_info, filename))
            else:
                print(f"⚠️  File not found: {filepath}")

        if not uploaded_docs:
            print("❌ No documents uploaded successfully")
            return

        # Step 4: Create translation jobs for priority languages
        print(f"\n🔄 CREATING TRANSLATION JOBS")
        print("-" * 30)

        translation_jobs = []

        # Test a manageable subset - English to other languages and vice versa
        test_combinations = []

        # English to other languages
        for target in PRIORITY_LANGUAGES:
            if target != 'en':
                test_combinations.append(('en', target))

        # Other languages to English
        for source in PRIORITY_LANGUAGES:
            if source != 'en':
                test_combinations.append((source, 'en'))

        print(f"📊 Testing {len(test_combinations)} language combinations across {len(uploaded_docs)} file formats")
        print(f"📊 Total jobs to create: {len(test_combinations) * len(uploaded_docs)}")

        # Create jobs for first document only initially to test the system
        test_doc = uploaded_docs[0]  # Use TXT file for initial testing
        doc_info, filename = test_doc

        print(f"\n🎯 TESTING WITH: {filename}")
        for source_lang, target_lang in test_combinations:
            job_info = self.create_translation_job(doc_info['id'], source_lang, target_lang)
            if job_info:
                translation_jobs.append((job_info, source_lang, target_lang, filename))

            # Small delay to avoid overwhelming the API
            time.sleep(0.1)

        print(f"\n✅ Created {len(translation_jobs)} translation jobs")

        # Step 5: Process all translation jobs
        print(f"\n⚙️  PROCESSING TRANSLATION JOBS")
        print("-" * 30)

        successful_jobs = []
        for job_info, source_lang, target_lang, filename in translation_jobs:
            job_id = job_info['id']
            print(f"Processing: {source_lang}→{target_lang} ({filename})")

            if self.process_translation_job(job_id):
                successful_jobs.append((job_info, source_lang, target_lang, filename))

            # Small delay between processing
            time.sleep(0.5)

        # Step 6: Download all completed translations
        print(f"\n⬇️  DOWNLOADING TRANSLATION RESULTS")
        print("-" * 30)

        downloaded_files = []
        for job_info, source_lang, target_lang, filename in successful_jobs:
            job_id = job_info['id']
            prefix = f"{os.path.splitext(filename)[0]}_{source_lang}_to_{target_lang}"

            filepath = self.download_translation(job_id, prefix)
            if filepath:
                downloaded_files.append((filepath, source_lang, target_lang, filename))

        # Step 7: Generate summary report
        print(f"\n📊 TEST SUMMARY REPORT")
        print("=" * 60)
        print(f"📄 Documents uploaded: {len(uploaded_docs)}")
        print(f"🔄 Translation jobs created: {len(translation_jobs)}")
        print(f"✅ Successful translations: {len(successful_jobs)}")
        print(f"⬇️  Files downloaded: {len(downloaded_files)}")

        if downloaded_files:
            print(f"\n📁 Downloaded translation files:")
            for filepath, source_lang, target_lang, filename in downloaded_files:
                print(f"   • {os.path.basename(filepath)} ({source_lang}→{target_lang})")

        print(f"\n🎯 MANUAL EVALUATION GUIDE")
        print("-" * 30)
        print("1. Check translation results in:", RESULTS_DIR)
        print("2. Compare translations across different languages")
        print("3. Verify technical terminology is preserved")
        print("4. Check for formatting consistency")
        print("5. Evaluate overall translation quality")

        print(f"\n✅ Comprehensive test completed!")
        return downloaded_files

if __name__ == "__main__":
    tester = TranslationTester()
    tester.run_comprehensive_test()