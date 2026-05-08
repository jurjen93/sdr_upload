from pprint import pprint
from datetime import date
from regions import Regions
from astropy.io import fits
from pathlib import Path
from json import load
from astropy.constants import c


def access_config():
    """
    Make access config
    """

    access_config = {
        "record": "public",  # or "public"
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
                    title,
                    funding,
                    sasid,
                    description,
                    authors,
                    software_version):
    """Create a record"""

    fits_meta = get_fits_meta(fits_file)
    polygon_ra, polygon_dec = get_polygon_coordinates(ds9_region)
    access = access_config()
    if funding is None:
        funding = []
    else:
        with open(funding) as f:
            funding = load(f)

    with open(authors) as f:
        authors_list = load(f)

    today = date.today().strftime("%Y-%m-%d")

    metadata = {
      "metadata": {
        "resource_type": { "id": "dataset" },
        "title": title,
        "publication_date": today,
        "creators": authors_list[0]['creators'],
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
          "funding": funding,
        "dates": [
          { "date": today, "type": { "id": "created" } },
          { "date": today, "type": { "id": "updated" } }
        ]
      },
      "access": access,
      "custom_fields": {
        "collection:metadata": {
          "accref": "TBD",
          "facet_id": str(facet_id),
          "instid": "LOFAR.HBA",
          "bandpassid": f"{int(round(fits_meta["central_freq_mhz"]-fits_meta['bandwidth_mhz']/2,0))}-"
                        f"{int(fits_meta["central_freq_mhz"]+fits_meta['bandwidth_mhz']/2+1)}",
          "bandpassrefval": c.value/(fits_meta["central_freq_mhz"]*1_000_000),
          "bandpassunit": "m",
          "bandpasshi": round(c.value/(round(fits_meta["central_freq_mhz"]+fits_meta['bandwidth_mhz']/2)*1_000_000), 4),
          "bandpasslo": round(c.value / (round(fits_meta["central_freq_mhz"]-fits_meta['bandwidth_mhz']/2)*1_000_000), 4),
          "imsize": [round(fits_meta["naxis1"]*abs(fits_meta['cdelt1']), 4), round(fits_meta["naxis2"]*abs(fits_meta['cdelt1']), 4)],
          "poly_ra": [str(p) for p in polygon_ra],
          "poly_dec": [str(p) for p in polygon_dec],
          "centeralpha": round(fits_meta["ra_deg"], 4),
          "centerdelta": round(fits_meta["dec_deg"], 4),
          "pixunits": fits_meta["pixel_units"],
          "wcs_equinox": fits_meta["wcs_equinox"],
          "wcs_projection": fits_meta["wcs_projection"],
          "refframe": "ICRS",
          "datafirstobs": fits_meta["date_obs"],
          "datelastobs": fits_meta["date_obs"],
          "related_products": "TBD"
    },
        "contact:email": [
          "jurjendejong@strw.leidenuniv.nl",
          "jong@astron.nl"],
          "extended:discipline": "Radio Astronomy"
      }
    }

    if sasid:
        metadata["custom_fields"]["collection:metadata"].update({"sasids": sasid})

    if description:
        with open(description) as f:
            description_text = f.read()
        metadata["metadata"].update({"description": description_text.replace("\n"," ")})
    else:
        metadata["metadata"].update({"description": ""})

    if software_version is not None:
        with open(software_version) as f:
            data = load(f)
            metadata['custom_fields']["collection:metadata"].update({'pipeline_version': data['version']})
            metadata['custom_fields']["collection:metadata"].update({'pipeline': data['remote']})
    pprint(metadata)

    return metadata
