from datetime import date
from json import load

def collection_metadata(title, authors):

    with open(authors) as f:
        authors_list = load(f)

    today = date.today().strftime("%Y-%m-%d")

    metadata = {
        "title": title,
        "resource_type": {"id": "collection"},
        "creators": authors_list,
        "publication_date": today
    }

    return metadata
