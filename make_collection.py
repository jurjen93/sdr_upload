from argparse import ArgumentParser
from sdr_requests.SDRsession import CreateCollection
from metadata.collection_metadata import collection_metadata


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Create a LOFAR-VLBI collection draft on SURF SDR.")

    # Collection information
    parser.add_argument("--record_ids", nargs="+", default=None,
                        help="Record IDs to link (always resolved to their latest published version). "
                             "Required for a new collection; with --new-version-of or "
                             "--update-draft, omit to use the currently linked records.")
    parser.add_argument("--title", required=True, help="Collection title.")
    parser.add_argument("--authors", required=True, help="Authors json file.")
    parser.add_argument("--description", required=True, help="Txt file with the collection description.")
    parser.add_argument("--funding", required=True, help="JSON file with funding information.")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl",
                        help="Base URL for the SDR instance.")

    # Draft handling (mutually exclusive)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--new-version-of", default=None,
                      help="ID of a published collection (record or parent ID). Creates a new "
                           "draft version of it; nothing is published.")
    mode.add_argument("--update-draft", default=None,
                      help="ID of an existing unpublished draft to overwrite "
                           "(e.g. a new-version draft you created earlier).")

    args = parser.parse_args()

    if args.new_version_of is None and args.update_draft is None and not args.record_ids:
        parser.error("--record_ids is required when creating a new collection.")

    return args


def main():
    """
    Main function
    """
    args = get_args()

    metadata = collection_metadata(args.title, args.authors, args.funding)
    SDRsesh = CreateCollection(args.url, args.token)

    if args.new_version_of:
        SDRsesh.new_collection_version(args.new_version_of, metadata,
                                       args.record_ids, args.description)
    elif args.update_draft:
        SDRsesh.update_collection_draft(args.update_draft, metadata,
                                        args.record_ids, args.description)
    else:
        SDRsesh.create_collection(metadata, args.record_ids, args.description)


if __name__ == "__main__":
    main()