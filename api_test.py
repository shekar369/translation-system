#!/usr/bin/env python3
"""
API Translation System Testing Script
Tests all document formats and key language translations.
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
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpassword123"

# Languages to test
TEST_LANGUAGES = ['en', 'es', 'fr', 'de', 'ja']

def main():
    print("API Translation System Test")
    print("=" * 40)

    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)

    session = requests.Session()

    # Step 1: Register/Login
    print("Step 1: Authentication")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }

    # Register user (might fail if exists)
    register_response = session.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Register status: {register_response.status_code}")

    # Login using token endpoint
    login_data = {
        "username": TEST_EMAIL,  # FastAPI OAuth2 uses 'username' field
        "password": TEST_PASSWORD
    }

    # Send as form data for OAuth2
    login_response = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    print(f"Login status: {login_response.status_code}")

    if login_response.status_code == 200:
        token_data = login_response.json()
        access_token = token_data['access_token']
        session.headers.update({'Authorization': f'Bearer {access_token}'})
        print("Authentication successful")
    else:
        print(f"Authentication failed: {login_response.text}")
        return

    # Step 2: Get supported languages
    print("\\nStep 2: Get supported languages")
    languages_response = session.get(f"{BASE_URL}/api/translate/languages")
    if languages_response.status_code == 200:
        languages_data = languages_response.json()
        supported_languages = languages_data['languages']
        print(f"Supported languages: {list(supported_languages.keys())}")
    else:
        print("Failed to get languages")
        return

    # Step 3: Upload test documents
    print("\\nStep 3: Upload test documents")
    test_files = [
        "ai-future-tech.txt",
        "ai-future-tech.html",
        "ai-future-tech.rtf",
        "ai-future-tech.pdf",
        "ai-future-tech.docx"
    ]

    uploaded_docs = []

    for test_file in test_files:
        file_path = os.path.join(TEST_DOCS_DIR, test_file)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue

        print(f"Uploading {test_file}...")

        with open(file_path, 'rb') as f:
            files = {'file': (test_file, f)}
            upload_response = session.post(f"{BASE_URL}/api/files/upload", files=files)

        if upload_response.status_code == 200:
            doc_info = upload_response.json()
            uploaded_docs.append((doc_info['id'], test_file))
            print(f"  SUCCESS - ID: {doc_info['id']}")
        else:
            print(f"  FAILED - Status: {upload_response.status_code}")
            print(f"  Error: {upload_response.text}")

    print(f"\\nUploaded {len(uploaded_docs)} documents")

    if not uploaded_docs:
        print("No documents uploaded successfully")
        return

    # Step 4: Create translation jobs (focus on TXT file first)
    print("\\nStep 4: Create translation jobs")

    # Use the first uploaded document (TXT) for testing
    doc_id, filename = uploaded_docs[0]
    print(f"Testing with: {filename} (ID: {doc_id})")

    translation_jobs = []

    # Create English to other language translations
    for target_lang in TEST_LANGUAGES:
        if target_lang != 'en':
            job_data = {
                "document_id": doc_id,
                "source_language": "en",
                "target_language": target_lang
            }

            print(f"Creating job: en -> {target_lang}")
            job_response = session.post(f"{BASE_URL}/api/translate/", json=job_data)

            if job_response.status_code == 200:
                job_info = job_response.json()
                translation_jobs.append((job_info['job_id'], 'en', target_lang))
                print(f"  SUCCESS - Job ID: {job_info['job_id']}")
            else:
                print(f"  FAILED - Status: {job_response.status_code}")
                print(f"  Error: {job_response.text}")

    print(f"\\nCreated {len(translation_jobs)} translation jobs")

    # Step 5: Check job status and process if needed
    print("\\nStep 5: Process translation jobs")
    successful_jobs = []

    for job_id, source_lang, target_lang in translation_jobs:
        print(f"Processing job {job_id}: {source_lang} -> {target_lang}")

        # Check if job needs processing
        process_response = session.post(f"{BASE_URL}/api/translate/jobs/{job_id}/process")

        if process_response.status_code == 200:
            result = process_response.json()
            print(f"  Process result: {result.get('message', 'Success')}")
            successful_jobs.append((job_id, source_lang, target_lang))
        else:
            print(f"  Process failed: {process_response.status_code}")
            print(f"  Error: {process_response.text}")

        time.sleep(2)  # Wait between processing

    # Step 6: Download results
    print("\\nStep 6: Download translation results")
    downloaded_files = []

    for job_id, source_lang, target_lang in successful_jobs:
        print(f"Downloading job {job_id}: {source_lang} -> {target_lang}")

        download_response = session.get(f"{BASE_URL}/api/translate/jobs/{job_id}/download")

        if download_response.status_code == 200:
            filename = f"translation_{source_lang}_to_{target_lang}_job_{job_id}.txt"
            filepath = os.path.join(RESULTS_DIR, filename)

            with open(filepath, 'wb') as f:
                f.write(download_response.content)

            downloaded_files.append(filename)
            print(f"  Downloaded: {filename}")
        else:
            print(f"  Download failed: {download_response.status_code}")

    # Step 7: Summary and evaluation guide
    print("\\n" + "=" * 40)
    print("TEST RESULTS SUMMARY")
    print("=" * 40)
    print(f"Documents uploaded: {len(uploaded_docs)}")
    print(f"Translation jobs created: {len(translation_jobs)}")
    print(f"Jobs processed: {len(successful_jobs)}")
    print(f"Files downloaded: {len(downloaded_files)}")

    if uploaded_docs:
        print("\\nUploaded documents:")
        for doc_id, filename in uploaded_docs:
            print(f"  - {filename} (ID: {doc_id})")

    if downloaded_files:
        print("\\nDownloaded translations:")
        for filename in downloaded_files:
            print(f"  - {filename}")

    print(f"\\nResults directory: {RESULTS_DIR}")

    print("\\nMANUAL EVALUATION CHECKLIST:")
    print("1. Open each translation file")
    print("2. Compare with original English content")
    print("3. Check technical terms (AI, Machine Learning, etc.)")
    print("4. Verify sentence structure and flow")
    print("5. Look for missing or incorrect translations")
    print("6. Rate overall quality (1-5 scale)")

    print("\\nTest completed successfully!")

if __name__ == "__main__":
    main()