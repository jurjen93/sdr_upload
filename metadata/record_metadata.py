from pprint import pprint
from datetime import date
from regions import Regions
from astropy.io import fits
from pathlib import Path


def access_config():
    """
    Make access config
    """

    access_config = {
        "record": "restricted",  # or "public"
        "files": "restricted",  # or "public"
    }

    return access_config


def get_fits_meta(fits_path):
    """
    Read metadata from a FITS header.
    """

    fits_path = Path(fits_path)

    with fits.open(fits_path) as hdul:
        header = hdul[0].header

    metadata = {
        "filename": fits_path.name,
        "telescope": header.get("TELESCOP"),
        "date_obs": header.get("DATE-OBS").split("T")[0],
        "object": header.get("OBJECT"),
        "ra_deg": float(header.get("CRVAL1")%360),   # reference RA
        "dec_deg": float(header.get("CRVAL2")),  # reference DEC
        "central_freq_mhz": float(round(header.get("CRVAL3")/1_000_000, 2)),
        "bandwidth_mhz": float(round(header.get("CDELT3")/1_000_000, 2)),
        "naxis": int(header.get("NAXIS")),
        "naxis1": int(header.get("NAXIS1")),
        "naxis2": int(header.get("NAXIS2")),
        "bmaj_arcsec": float(round(header.get("BMAJ") * 3600, 2)),
        "bmin_arcsec": float(round(header.get("BMIN") * 3600, 2)),
        "bpa_deg": float(round(header.get("BPA"), 2)),
        "cdelt1": float(header.get("CDELT1")),
        "cdelt2": float(header.get("CDELT2")),
        "pixel_units": str(header.get("BUNIT")),
        "imaging_software": header.get("ORIGIN"),
        "wcs_equinox": str(header.get("EQUINOX")),
        "wcs_projection": "SIN"
    }

    return metadata


def get_polygon_coordinates(region_file):
    """
    Extract polygon coordinates from a DS9 region file.

    Parameters
    ----------
    region_file : str
        Path to DS9 region file.

    Returns
    -------
    coords : list of tuples
    """

    reg = Regions.read(region_file)
    ra = reg[0].vertices.ra.value
    dec = reg[0].vertices.dec.value

    return ra, dec


def get_record_metadata(fits_file,
                    ds9_region,
                    facet_id,
                    title):
    """Create a record"""

    fits_meta = get_fits_meta(fits_file)
    pprint(fits_meta)
    polygon_ra, polygon_dec = get_polygon_coordinates(ds9_region)
    access = access_config()

    today = date.today().strftime("%Y-%m-%d")

    metadata = {
      "metadata": {
        "resource_type": { "id": "dataset" },
        "title": title,
        "description": f"<DESCRIPTION>\n\nThese are the FITS files corresponding to facet {facet_id}",
        "publication_date": today,
        "creators": [
          {
            "person_or_org": {
              "name": "J.M.G.H.J. de Jong",
              "type": "personal",
              "given_name": "J.M.G.H.J.",
              "family_name": "de Jong"
            }
          }
        ],
        "subjects": [
          { "subject": "surveys" },
          { "subject": "catalogues" },
          { "subject": "radio continuum: general" },
          { "subject": "techniques: image processing" }
        ],
        "publication_date": today,
        "publisher": "Leiden Observatory",
        "language": "eng",
        "rights": [
          {
            "link": "http://creativecommons.org/licenses/by-sa/4.0/",
            "title": {
              "en": "Creative Commons Attribution-ShareAlike (CC-BY-SA)"
            }
          }
        ],
          "funding": [
              {
                  "funder": {
                      "name": "OSCARS project", # TODO: Update?
                      "identifier": "https://oscars-project.eu/projects/copli-creating-fair-open-science-pipeline-high-resolution-lofar-imaging",
                      "scheme": "ror"
                  }
              }
          ],
        "dates": [
          { "date": today, "type": { "id": "created" } },
          { "date": today, "type": { "id": "updated" } }
        ]
      },
      "custom_fields": {
        "collection:metadata": {
          "telescope": "LOFAR.HBA",
          "central_freq_mhz": fits_meta["central_freq_mhz"],
          "bandwidth_mhz": fits_meta['bandwidth_mhz'],
          "image_size": [fits_meta["naxis1"], fits_meta["naxis2"]],
          "pixel_units": fits_meta["pixel_units"],
          "pixel_scale": [abs(fits_meta['cdelt1']), abs(fits_meta['cdelt2'])],
          "polygon_ra": ','.join([str(p) for p in polygon_ra]),
          "polygon_dec": ','.join([str(p) for p in polygon_dec]),
          "facet_id": str(facet_id),
          "imaging_software": fits_meta["imaging_software"],
          "data_reduction_pipeline": "pilot (https://github.com/LOFAR-VLBI/pilot)",
          "data_reduction_pipeline_commit": "282638e",
          "wcs_equinox": fits_meta["wcs_equinox"],
          "observing_data": fits_meta["date_obs"],
          "wcs_projection": fits_meta["wcs_projection"],
          "naxis": fits_meta["naxis"]
        },
        "access": access,
        "contact:email": [
          "jurjendejong@strw.leidenuniv.nl",
          "jong@astron.nl"]
      }
    }

    # TODO: Add related work?

    return metadata
