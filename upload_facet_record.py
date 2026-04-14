from argparse import ArgumentParser
from sdr_requests.SDRsession import UploadRecord
from metadata.record_metadata import get_record_metadata


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    # Required file information
    parser.add_argument("--fits", nargs="+", required=True, help="Path to the FITS file(s).")
    parser.add_argument("--region", required=True, help="Path to the ds9 region file.")
    parser.add_argument("--merged-h5", nargs="+", required=True, help="Path to h5parm solution file(s).")
    parser.add_argument("--facet-id", required=True, help="Facet ID (e.g. 1).")
    parser.add_argument("--title", required=True, help="Base title of the record. This is extended with -facet_<facet-id>.")
    parser.add_argument("--funding", required=True, help="Json file with funding information")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    # Actions
    parser.add_argument("--add-pid", action="store_true", help="Reserve a DOI for the record.")
    parser.add_argument("--publish", action="store_true", help="Publish the record (Draft -> Public).")

    return parser.parse_args()


def upload_record(fits_files, region, merged_h5, facet_id, url, add_pid, publish, title, token, funding):

    files_to_upload = [region] + fits_files
    if merged_h5 is not None:
        files_to_upload.append(merged_h5)

    SDRsesh = UploadRecord(url, token)

    # Get metadata
    metadata = get_record_metadata(fits_files[0],
                                   region,
                                   facet_id,
                                   title+f"-facet_{facet_id}",
                                   funding)

    # Create a record
    record = SDRsesh.create_record(metadata)

    # Create PID for record
    if add_pid:
        SDRsesh.add_pid(record['id'])

    # Add files
    SDRsesh.add_files(files_to_upload, record["id"])

    # Publish data
    if publish:
        SDRsesh.publish_record(record["id"])


def main():
    """
    Main function
    """

    args = get_args()
    upload_record(args.fits,
                  args.region,
                  args.merged_h5,
                  args.facet_id,
                  args.url,
                  args.add_pid,
                  args.publish,
                  args.title,
                  args.token,
                  args.funding)

if __name__ == "__main__":
    main()
