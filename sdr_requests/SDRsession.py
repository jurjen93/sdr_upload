import requests
import json
from os import path
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class UploadRecord:
    def __init__(self, BASE_URL=None, TOKEN_FILE=None):

        self.BASE_URL = BASE_URL if BASE_URL is None else "https://sdr-acc.repository.surf.nl"

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
            print(f"Error: {response.status_code} - {response.text}")
            return None

    def add_pid(self, record_id):
        """Add a PID to record"""

        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/pids/doi",
            headers=self.headers
        )
        r.raise_for_status()
        draft_record = r.json()

        print("Reserved DOI -> ", draft_record["pids"]["doi"]["identifier"])

    def add_files(self, file_list, record_id):
        """
        Initialize and upload multiple files for a single record.
        """

        init_data = [{"key": path.basename(f)} for f in file_list]

        print(f"Initializing {len(file_list)} files...")
        r = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/files",
            json=init_data,
            verify=False,
            headers=self.headers
        )
        r.raise_for_status()

        # Get the response
        response_data = r.json()

        for file_path in file_list:
            file_key = path.basename(file_path)

            # Find the links for this specific file key from the response
            file_entry = next(e for e in response_data['entries'] if e['key'] == file_key)
            url_content = file_entry['links']['content']
            url_commit = file_entry['links']['commit']

            # Uploading
            upload_headers = self.headers.copy()
            upload_headers["Content-Type"] = "application/octet-stream"

            print(f"Uploading: {file_key}...")
            with open(file_path, 'rb') as f:
                r_upload = requests.put(
                    url_content,
                    headers=upload_headers,
                    data=f,
                    verify=False
                )
            r_upload.raise_for_status()

            # Committing
            print(f"Committing: {file_key}...")
            r_commit = requests.post(
                url_commit,
                headers=self.headers,
                verify=False
            )
            r_commit.raise_for_status()
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

    def create_secret_link(self, record_id, permission="view", expires_at=None):
        """
        FROM: https://servicedesk.surf.nl/wiki/spaces/WIKI/pages/269649032/Sharing+draft+records+with+invenio+using+the+API#SharingdraftrecordswithinveniousingtheAPI-CreateaSecretLink
        Create a secret link for a draft.

        Args:
            record_id: The ID of the record
            permission: "view" or "edit"
            expires_at: Optional expiration datetime (ISO format)

        Returns:
            Dict with link information including the token
        """

        link_data = {
            "permission": permission
        }

        # Add expiration if provided
        if expires_at:
            link_data["expires_at"] = expires_at

        response = requests.post(
            f"{self.BASE_URL}/api/records/{record_id}/draft/access/links",
            headers=self.headers,
            data=json.dumps(link_data)
        )

        if response.status_code == 201:
            link_info = response.json()
            token = link_info.get("token")

            # Construct the shareable URL
            share_url = f"{self.BASE_URL}/uploads/{record_id}?token={token}"
            print(share_url)

            print(f"Secret link created!")
            print(f"Share URL: {share_url}")
            print(f"Token: {token}")
            print(f"Permission: {permission}")

            return {
                "token": token,
                "share_url": share_url,
                "permission": permission,
                "link_info": link_info
            }
        else:
            print(f"Error creating link: {response.status_code} - {response.text}")
            return None


class CreateCollection(UploadRecord):
    def __init__(self, BASE_URL=None, TOKEN_FILE=None):
        super().__init__(BASE_URL, TOKEN_FILE)

    def create(self, metadata, record_ids):
        """Creates a collection record linking to existing record IDs."""
        api_url = f"{self.BASE_URL}/api/records"

        data = {
            "files": {"enabled": False},
            "metadata": metadata,
            "custom_fields": {
                "collection:records": record_ids
            }
        }

        response = requests.post(api_url, headers=self.headers, json=data, verify=False)

        if response.status_code == 201:
            res = response.json()
            print(f"Collection {metadata['title']} created successfully!")
            print(f"ID: {res.get('id')}")
            return res
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
