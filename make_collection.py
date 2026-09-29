from argparse import ArgumentParser
from sdr_requests.SDRsession import CreateCollection
from metadata.collection_metadata import collection_metadata


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    # Required file information
    parser.add_argument("--record_ids", nargs="+", required=True, help="Record IDs")
    parser.add_argument("--title", required=True, help="Collection title.")
    parser.add_argument("--authors", required=True, help="Authors json file")
    parser.add_argument("--description", required=True, help="Add description to upload from input txt file.")
    parser.add_argument("--funding", required=True, help="JSON file with funding information.")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    # Versioning
    parser.add_argument("--new-version-of", default=None,
                        help="Record ID of an existing published record. If given, creates a new version "
                             "of that record instead of a brand new record.")

    # Actions
    # parser.add_argument("--add-pid", action="store_true", help="Reserve a DOI for the record.")
    # parser.add_argument("--publish", action="store_true", help="Publish the record (Draft -> Public).")

    return parser.parse_args()


def main():
    """
    Main function
    """

    args = get_args()

    metadata = collection_metadata(args.title, args.authors, args.funding)
    SDRsesh = CreateCollection(args.url, args.token)
    if args.new_version_of:
        record = SDRsesh.new_version(args.new_version_of)

        payload = dict(metadata)
        payload["files"] = {"enabled": record["files"]["enabled"]}

        SDRsesh.update_metadata(record["id"], payload)
    else:
        SDRsesh.create_collection(metadata, args.record_ids, args.description)

if __name__ == "__main__":
    main()
