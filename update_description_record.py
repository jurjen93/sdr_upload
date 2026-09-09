from argparse import ArgumentParser
from sdr_requests.SDRsession import UploadRecord


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Update only the description of an existing SURF SDR record.")

    parser.add_argument("--record-id", required=True, help="ID of the record to update (draft or published).")
    parser.add_argument("--description", required=True, help="Path to the new description .txt file.")
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")
    parser.add_argument('--extra-text', help='Add extra text to the record')
    return parser.parse_args()


def load_description_html(description_path, facet_id=None, extra_text=None):
    with open(description_path) as f:
        text = f.read().strip()

    paragraphs = [p.strip().replace("\n", " ") for p in text.split("\n\n") if p.strip()]

    if facet_id is not None and facet_id!="N/A":
        facet_text = (
            f"Below you find the dirty, model, residual, RMS, PSF, and primary-beam "
            f"corrected Stokes-I images from <strong>facet {facet_id}</strong> at "
            f"0.3″, 0.6″, and 1.2″."
        )
        paragraphs.append(facet_text)

    if extra_text is not None:
        paragraphs.append(extra_text)

    return "".join(f"<p>{p}</p>" for p in paragraphs)


def update_description(record_id, description_path, token, url, extra_text):
    SDRsesh = UploadRecord(url, token)

    # Check current state of the record to decide whether we need to open a draft first
    record = SDRsesh.get_record(record_id)
    is_published = record.get("is_published", False)

    if is_published:
        print(f"Record {record_id} is published. Opening an edit-draft...")
        record = SDRsesh.edit_published_record(record_id)
    else:
        print(f"Record {record_id} is already a draft. Editing in place...")

    # Fetch the current draft state (full metadata payload), so we only change description
    draft = SDRsesh.get_record(record_id)  # works for drafts too, but see note below

    facet_id = draft.get("custom_fields", {}) \
                    .get("collection:metadata", {}) \
                    .get("facet_id")
    print(f"FACET {facet_id}")
    new_description = load_description_html(description_path, facet_id, extra_text)
    draft["metadata"]["description"] = new_description

    payload = {
        "metadata": draft["metadata"],
        "access": draft["access"],
        "custom_fields": draft["custom_fields"],
        "files": {"enabled": draft["files"]["enabled"]}
    }

    print("Updating description...")
    SDRsesh.update_metadata(record_id, payload)

    SDRsesh.publish_record(record_id)


def main():
    args = get_args()
    update_description(args.record_id,
                       args.description,
                       args.token,
                       args.url,
                       args.extra_text)


if __name__ == "__main__":
    main()