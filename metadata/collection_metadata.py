from datetime import date

def collection_metadata(title):

    today = date.today().strftime("%Y-%m-%d")

    metadata = {
        "title": title,
        "resource_type": {"id": "collection"},
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
        "publication_date": today
    }

    return metadata
