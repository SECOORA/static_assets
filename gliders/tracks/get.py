#!/usr/bin/env python
# coding=utf-8

# conda execute
# env:
#  - fiona
#  - geojson
#  - requests
# channels:
#  - conda-forge
# run_with: python

"""
Create GeoJSON Features for SECOORA Stations.

To test the features copy-and-paste the GeoJSON file onto:

http://geojson.io/

Run with,
$ conda execute -v convert.py

"""

import os

import fiona
import geojson
import requests
from fiona.crs import from_epsg

import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def main():

    # These are UUIDs in to the platforms system (platforms.axds.co)
    groups = {
        'gliders_2016': [
            'ddc8a6b9-ad02-419d-bc7e-795ed41ec6f6',  # ramses-20160909T2028
            'd6dddbd3-d93b-44c9-97bb-0d391d170227',  # bass-20160909T1733
            '47fa07c5-e1cd-4265-baab-19e1255106b4',  # modena-20160909T1758
            'e63eba82-3a8a-427e-9f0e-14f150a1dbe6',  # salacia-20160919T2028
        ]
    }

    keep_globals = [
        'contributor_name',
        'platform_type',
        'vessel_name',
        'institution',
        'naming_authority',
        'id',
        'title'
    ]

    for g, uids in groups.items():
        features = []
        for uid in uids:
            url = 'http://platforms.axds.co/platforms/{}'.format(uid)
            r = requests.get(url, params={'verbose': True}).json()
            features.append(geojson.Feature(
                geometry=r.get('geometry'),
                properties={ k: v for k, v in r.get('metadata').get('global').items() if k in keep_globals }
            ))

        save_geojson(g, features)
        save_shapefile(g, features)


def save_geojson(name, features):
    fc = geojson.FeatureCollection(features)
    os.makedirs(name, exist_ok=True)
    with open('{name}/{name}.geojson'.format(name=name), 'w') as f:
        geojson.dump(fc, f, sort_keys=True, indent=2, separators=(",", ": "))


def save_shapefile(name, features):

    def shape_name(name):
        return name.lower()[:10]

    keys = set()
    for f in features:
        for k, v in f.properties.items():
            keys.add(k)
    keys = [ (k[0:9], 'str') for k in keys ]

    schema = {
        'geometry': 'LineString',
        'properties': keys
    }

    os.makedirs(name, exist_ok=True)
    with fiona.open('{name}/{name}.shp'.format(name=name), "w",
                    driver="ESRI Shapefile",
                    crs=from_epsg(4326),
                    schema=schema) as f:
        for t in features:
            f.write({
                "geometry": t.geometry,
                "properties": { k[0:9]: str(v) for k, v, in t.properties.items() }
            })


if __name__ == "__main__":
    main()
