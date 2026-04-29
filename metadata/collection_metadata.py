from datetime import date

def collection_metadata(title, authors):

    today = date.today().strftime("%Y-%m-%d")

    metadata = {
        "title": title,
        "resource_type": {"id": "collection"},
        "creators": [
            authors[0]
        ],
        "publication_date": today
    }

    return metadata
