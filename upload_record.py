from argparse import ArgumentParser
from sdr_requests.SDRsession import UploadRecord
from metadata.record_metadata import get_record_metadata
from datetime import date


def get_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="Upload LOFAR-VLBI data to SURF SDR.")

    # Required file information
    parser.add_argument("--fits", nargs="+", required=True, help="Path to the FITS file(s).")
    parser.add_argument("--region", required=True, help="Path to the ds9 region file.")
    parser.add_argument("--merged-h5", nargs="+", help="Path to h5parm solution file(s).")
    parser.add_argument("--upload_only_other_files", action="store_true", help="Use FITS file only for metadata")
    parser.add_argument("--other_files", nargs="+", help="Use FITS file only for metadata")
    parser.add_argument("--facet-id", required=True, help="Facet ID (e.g. 1).")
    parser.add_argument("--title", required=True, help="Base title of the record. This is extended with -facet_<facet-id>.")
    parser.add_argument("--funding", required=True, help="JSON file with funding information.")
    parser.add_argument("--sasid", required=True, help="SAS ID(s) from observations.")
    parser.add_argument("--authors", required=True, help="JSON file with author information.")
    parser.add_argument("--description", required=True, help="Add description to upload from input txt file.")
    parser.add_argument("--software-version", help="JSON with software versioning information. This can be generated with lofar_helpers (using the cwl_provenance tool)")

    # Versioning
    parser.add_argument("--new-version-of", default=None,
                        help="Record ID of an existing published record. If given, creates a new version "
                             "of that record instead of a brand new record.")

    # Configuration
    parser.add_argument("--token", required=True, help="Path to SDR token file.")
    parser.add_argument("--url", default="https://sdr-acc.repository.surf.nl", help="Base URL for the SDR instance.")

    # Actions
    parser.add_argument("--add-pid", action="store_true", help="Reserve a DOI for the record.")
    parser.add_argument("--publish", action="store_true", help="Publish the record (Draft -> Public).")

    return parser.parse_args()


def upload_record(fits_files, region, merged_h5, facet_id, url, add_pid, publish,
                  title, token, funding, sasid, description, authors, software_version, upload_only_other_files,
                  other_files, new_version_of):

    files_to_upload = []
    if not upload_only_other_files:
        files_to_upload += [region] + fits_files
        if merged_h5 is not None:
            for h5 in merged_h5:
                files_to_upload.append(h5)
    if other_files is not None:
        files_to_upload += other_files

    SDRsesh = UploadRecord(url, token)

    # Get metadata
    metadata = get_record_metadata(fits_files[0],
                                   region,
                                   facet_id,
                                   title,
                                   funding,
                                   sasid,
                                   description,
                                   authors,
                                   software_version)
    if new_version_of:
        # Fetch the original record to preserve its creation date
        original = SDRsesh.get_record(new_version_of)
        original_created = next(
            (d["date"] for d in original["metadata"].get("dates", [])
             if d["type"]["id"] == "created"),
            None
        )

        if original_created:
            metadata["metadata"]["dates"] = [
                {"date": original_created, "type": {"id": "created"}},
                {"date": date.today().strftime("%Y-%m-%d"), "type": {"id": "updated"}}
            ]

        # Create a new draft version linked to the existing record
        record = SDRsesh.new_version(new_version_of)

        payload = dict(metadata)
        payload["files"] = {"enabled": record["files"]["enabled"]}

        record = SDRsesh.update_metadata(record["id"], payload)
    else:
        # Create a brand new record
        record = SDRsesh.create_record(metadata)

    # Create PID for record
    if add_pid: SDRsesh.add_pid(record['id'])
    # Add files
    SDRsesh.add_files(files_to_upload, record["id"])
    # Publish data
    if publish: SDRsesh.publish_record(record["id"])


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
                  args.funding,
                  args.sasid,
                  args.description,
                  args.authors,
                  args.software_version,
                  args.upload_only_other_files,
                  args.other_files,
                  args.new_version_of)

if __name__ == "__main__":
    main()
