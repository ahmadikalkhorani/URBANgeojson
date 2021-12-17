import requests
from bs4 import BeautifulSoup as bs
import numpy as np
from joblib import Parallel, delayed
import json
import datetime
import xmltodict



def getFeature(BuildingAddress):
    properties, coordinates = getBuidingInfoFromOSM(BuildingAddress)

    if isinstance(coordinates, np.ndarray):
        coordinates = coordinates.tolist()

    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [coordinates]
        },
        "properties": properties
    }


def getCoordinates(buildingID, transform=True):
    url = 'https://www.openstreetmap.org/way/'+str(buildingID)

    soup = bs(requests.get(url).content, 'html.parser')
    node_list = [int(node.text)
                 for node in soup.find_all("a", {"class": "node"})]

    url = requests.get(
        'https://www.openstreetmap.org/api/0.6/way/'+str(buildingID)+'/full').content
    soup = bs(url, 'xml')
    nodes = soup.find_all('node')
    coordinates = [(int(node['id']), float(node['lat']),
                    float(node['lon'])) for node in nodes]
    coordinates = np.array(coordinates)[np.searchsorted(
        np.array(coordinates)[:, 0], np.array(node_list))][:, 1:]

    return np.flip(coordinates)


def getValue(dict, key):
    defualt_values = {
        'category': 'building',
        'display_name': None,
    }

    try:
        return dict[key]
    except:
        return defualt_values[key]


def PolyArea(Coordinates):
    try:
        x, y = Coordinates[:, 0], Coordinates[:, 1]
        return 0.5*np.abs(np.dot(x, np.roll(y, 1))-np.dot(y, np.roll(x, 1)))
    except:
        return None


def PolyPerimeter(Coordinates):
    try:
        Coordinates = np.append(Coordinates, [Coordinates[0, :]], axis=0)
        return np.sum(np.power(Coordinates[1:, :] - Coordinates[:-1, :], 2), axis=1).sum()
    except:
        return None


def getBuidingInfoFromOSM(buildingAddress):
    BuildingNameForSearch = buildingAddress
    url = f'https://nominatim.openstreetmap.org/search.php?q={BuildingNameForSearch}&format=jsonv2'
    soup = bs(requests.get(url).content, 'html.parser')
    data = json.loads(requests.get(url).content)[0]

    osm_id = data['osm_id']

    url2 = 'https://www.openstreetmap.org/api/0.6/way/'+str(osm_id)
    content = requests.get(url2).content
    try:
        levels = [int(tag['@v']) for tag in xmltodict.parse(content)
                  ['osm']['way']['tag'] if 'levels' in tag['@k']][0]
        levels = int(levels)
        height = 2.8 * levels
    except:
        levels = None
        height = None

    coordinates = getCoordinates(buildingID=osm_id, transform=False)
    coordinates_trans = getCoordinates(buildingID=osm_id, transform=True)

    properties = {
        'id': getValue(dict=data, key='osm_id'),
        'type': getValue(dict=data, key='category'),
        'geometryType': "Polygon",
        'name': getValue(dict=data, key='display_name').split(',')[0],
        'footprint_area': PolyArea(coordinates_trans),
        'footprint_perimeter': PolyPerimeter(coordinates_trans),
        'project_id': None,
        'updated_at': datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%I'),
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%I'),
        'building_type': data['type'],
        'number_of_stories': levels,
        'height': height,
        'number_of_stories_above_ground': None,
        'building_status': None,
        'include_in_energy_analysis': True,
        'floor_area': None,
        'year_built': None,
    }

    return properties, coordinates

def buildingFeature(bldg):
    try:
        return getFeature(bldg)
    except:
        print(f'Error in finding data for : {bldg}\n')
        return None


def urbanGeoJson(buildingsAdressList, save_to=None):
    geoJson = {
        "type": "FeatureCollection",
        "features": Parallel(n_jobs=-2)(delayed(buildingFeature)(bldg) for bldg in buildingsAdressList)
    }
    if save_to is not None:
        with open('test.json', "w") as write_file:
            json.dump(geoJson, write_file)
    return geoJson
