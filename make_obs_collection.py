from argparse import ArgumentParser
from sdr_requests.SDRsession import CreateCollection
from metadata.collection_metadata import collection_metadata
from .upload_facet_record import upload_record


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    # Required file information
    parser.add_argument("--fits", nargs="+", required=True, help="Path to the FITS file.")
    parser.add_argument("--region", nargs="+", required=True, help="Path to the ds9 region file.")
    parser.add_argument("--title", required=True, help="Collection title and base title of the record. "
                                                       "Record title is extended with -facet_<facet-id>.")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    # Actions
    parser.add_argument("--add-pid", action="store_true", help="Reserve a DOI for the record.")
    parser.add_argument("--publish", action="store_true", help="Publish the record (Draft -> Public).")

    return parser.parse_args()


def main():
    """
    Main function
    """

    args = get_args()

    files_to_upload = args.region + args.fits

    # TODO: Sort out different records
    # TODO: Upload record
    # TODO: Make Collection

if __name__ == "__main__":
    main()
