from argparse import ArgumentParser
from sdr_requests.SDRsession import CreateCollection
from metadata.collection_metadata import collection_metadata
from json import load


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    # Required file information
    parser.add_argument("--record_ids", nargs="+", required=True, help="Record IDs")
    parser.add_argument("--title", required=True, help="Collection title.")
    parser.add_argument("--authors", required=True, help="Authors json file")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    # Actions
    # parser.add_argument("--add-pid", action="store_true", help="Reserve a DOI for the record.")
    # parser.add_argument("--publish", action="store_true", help="Publish the record (Draft -> Public).")

    return parser.parse_args()


def main():
    """
    Main function
    """

    args = get_args()

    with open(args.authors) as f:
        authors = load(f)

    metadata = collection_metadata(args.title, authors)
    SDRsesh = CreateCollection(args.url, args.token)
    SDRsesh.create(metadata, args.record_ids)

if __name__ == "__main__":
    main()
