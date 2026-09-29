from argparse import ArgumentParser
from sdr_requests.SDRsession import CreateCollection
from metadata.collection_metadata import collection_metadata


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    parser.add_argument("--record_ids", nargs="+", default=None,
                        help="Record IDs. Required for a new collection; for a new version, "
                             "omit to keep the records of the previous version.")
    parser.add_argument("--title", required=True, help="Collection title.")
    parser.add_argument("--authors", required=True, help="Authors json file")
    parser.add_argument("--description", required=True, help="Add description to upload from input txt file.")
    parser.add_argument("--funding", required=True, help="JSON file with funding information.")

    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    parser.add_argument("--new-version-of", default=None,
                        help="Record ID of an existing published collection. If given, creates a new "
                             "version of that collection instead of a brand new one.")

    return parser.parse_args()


def main():
    args = get_args()

    metadata = collection_metadata(args.title, args.authors, args.funding)
    SDRsesh = CreateCollection(args.url, args.token)

    if args.new_version_of:
        SDRsesh.new_collection_version(args.new_version_of, metadata,
                                       args.record_ids, args.description)
    else:
        SDRsesh.create_collection(metadata, args.record_ids, args.description)


if __name__ == "__main__":
    main()