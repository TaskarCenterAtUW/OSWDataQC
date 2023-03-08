import requests

def get_changesets():
    bbox = "51.47 -0.01 51.477 0.01 51.484 -0.01\
  51.483 -0.0093 51.471 -0.0093 51.477 0.008\
  51.483 -0.0093 51.484 -0.01"
    query = f"""
        [out:xml][timeout:25];
        (
          node["changeset"]["poly"="{bbox}"];
          way["changeset"]["poly"="{bbox}"];
          relation["changeset"]["poly"="{bbox}"];
        );
        out body;
    """
    response = requests.get(f'http://overpass-api.de/api/interpreter', params={'data': query})
    return response.text

changesets = get_changesets()
print(changesets)
