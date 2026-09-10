import requests
import json
from os import path
import urllib3
import sys
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UploadRecord:
    def __init__(self, BASE_URL=None, TOKEN_FILE=None):

        self.BASE_URL = "https://sdr-acc.repository.surf.nl" if BASE_URL is None else BASE_URL

        with open(TOKEN_FILE) as f:
            self.headers = {"Authorization": f"Bearer {f.read().strip()}",
                            "Content-Type": "application/json"}

    def create_record(self, metadata):
        """Create a record"""


        response = requests.post(
            f"{self.BASE_URL}/api/records",
            headers=self.headers,
            data=json.dumps(metadata)
        )

        if response.status_code == 201:
            draft = response.json()
            return draft
        else:
            sys.exit(f"Error: {response.status_code} - {response.text}")

    def get_record(self, record_id):
        """Fetch a record (published or draft) by ID."""
        r = requests.get(
            f"{self.BASE_URL}/api/records/{record_id}",
            headers=self.headers,
            verify=False
        )
        r.raise_for_status()
        return r.json()

    def new_version(self, record_id):
        """
        Create a new draft version linked to an existing published record.
        Returns the new draft (with its own record id, but the same parent).
        """
        print(f"Creating new version from record {record_id}...")

        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/versions",
            headers=self.headers,
            verify=False
        )
        r.raise_for_status()

        new_draft = r.json()
        print(f"New draft version created: {new_draft['id']}")
        print(f"(Parent/concept id: {new_draft['parent']['id']})")

        return new_draft

    def edit_published_record(self, record_id):
        """
        Open an edit-draft of an already-published record.
        """
        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft",
            headers=self.headers,
            verify=False
        )
        r.raise_for_status()
        return r.json()

    def update_metadata(self, record_id, metadata):
        """
        Update metadata on a draft (e.g. the new version draft).
        """
        r = requests.put(
            f"{self.BASE_URL}/api/records/{record_id}/draft",
            headers=self.headers,
            data=json.dumps(metadata),
            verify=False
        )
        r.raise_for_status()
        return r.json()

    def add_pid(self, record_id):
        """Add a PID to record"""

        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/pids/doi",
            headers=self.headers
        )
        r.raise_for_status()
        draft_record = r.json()

        print("Reserved DOI -> ", draft_record["pids"]["doi"]["identifier"])

    def add_files(self, file_list, record_id, max_retries=5, backoff_base=15,
                  connect_timeout=30, read_timeout=3600):
        """
        Initialize and upload multiple files for a single record.
        Retries transient network failures with exponential backoff, and skips
        files that are already fully committed on the draft (resume support).
        """
        timeout = (connect_timeout, read_timeout)

        already_done = set()
        r = requests.get(
            f"{self.BASE_URL}/api/records/{record_id}/draft/files",
            headers=self.headers,
            verify=False
        )
        if r.status_code == 200:
            for entry in r.json().get("entries", []):
                if entry.get("status") == "completed":
                    already_done.add(entry["key"])

        remaining = [f for f in file_list if path.basename(f) not in already_done]
        skipped = [f for f in file_list if path.basename(f) in already_done]
        if skipped:
            print(f"Skipping {len(skipped)} already-uploaded file(s): "
                  f"{[path.basename(f) for f in skipped]}")

        if not remaining:
            print("All files already uploaded.")
            return

        # --- Initialize remaining files ---
        init_data = [{"key": path.basename(f)} for f in remaining]

        print(f"Initializing {len(remaining)} file(s)...")
        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/files",
            json=init_data,
            verify=False,
            headers=self.headers,
            timeout=timeout
        )
        r.raise_for_status()
        response_data = r.json()

        for file_path in remaining:
            file_key = path.basename(file_path)
            file_entry = next(e for e in response_data['entries'] if e['key'] == file_key)
            url_content = file_entry['links']['content']
            url_commit = file_entry['links']['commit']

            upload_headers = self.headers.copy()
            upload_headers["Content-Type"] = "application/octet-stream"

            # --- Upload content, with retry/backoff ---
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"Uploading: {file_key} (attempt {attempt}/{max_retries})...")
                    with open(file_path, 'rb') as f:
                        r_upload = requests.put(
                            url_content,
                            headers=upload_headers,
                            data=f,
                            verify=False,
                            timeout=timeout
                        )
                    r_upload.raise_for_status()
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"  Upload failed: {e}")
                    if attempt == max_retries:
                        raise
                    sleep_time = backoff_base * attempt
                    print(f"  Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

            # --- Commit, with retry/backoff ---
            for attempt in range(1, max_retries + 1):
                try:
                    print(f"Committing: {file_key} (attempt {attempt}/{max_retries})...")
                    r_commit = requests.post(
                        url_commit,
                        headers=self.headers,
                        verify=False,
                        timeout=timeout
                    )
                    r_commit.raise_for_status()
                    break
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    print(f"  Commit failed: {e}")
                    if attempt == max_retries:
                        raise
                    sleep_time = backoff_base * attempt
                    print(f"  Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)

            print(f"Finished: {file_key}")

    def publish_record(self, record_id):
        """
        Publish the draft record to make it public and permanent.
        """
        print(f"Publishing record {record_id}...")

        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/actions/publish",
            headers=self.headers,
            verify=False
        )
        r.raise_for_status()

        published_record = r.json()
        print(f"Record successfully published!")
        print(f"Permanent URL: {published_record['links']['self_html']}")

        return published_record


class CreateCollection(UploadRecord):
    def __init__(self, BASE_URL=None, TOKEN_FILE=None):
        super().__init__(BASE_URL, TOKEN_FILE)

    def create(self, metadata, record_ids, description=None):
        """Creates a collection record linking to existing record IDs."""
        api_url = f"{self.BASE_URL}/api/records"

        metadata = {
            "files": {"enabled": False},
            "metadata": metadata,
            "custom_fields": {
                "collection:records": record_ids,
            "contact:email": [
                "jurjendejong@strw.leidenuniv.nl",
                "jong@astron.nl"]
            }
        }

        if description is not None:
            with open(description) as f:
                description_text = f.read()
            metadata["metadata"].update({"description": description_text.replace("\n", " ")})
        else:
            metadata["metadata"].update({"description": ""})

        response = requests.post(api_url, headers=self.headers, json=metadata, verify=False)

        if response.status_code == 201:
            res = response.json()
            print(f"Collection {metadata['metadata']['title']} created successfully!")
            print(f"ID: {res.get('id')}")
            return res
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
