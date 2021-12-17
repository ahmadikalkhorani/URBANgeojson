from URBANgeojson import urbanGeoJson

buildings = [
    'Raney House Columbus Ohio',
    'Busch House Columbus Ohio',
    'Nosker House Columbus Ohio',
    'Taylor Tower Columbus Ohio',
    'Houston House Columbus Ohio',
    'Physics Research Building Columbus Ohio'
]


geoJson = urbanGeoJson(buildingsAdressList = buildings, save_to = 'test.json')

