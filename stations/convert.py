#!/usr/bin/env python
# coding=utf-8

# conda execute
# env:
#  - fiona
#  - geojson
#  - pandas
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

import fiona
import geojson
import numpy as np
import pandas as pd

import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)

status_colors = {
    'Planned':      'orange',
    'Operational':  'green',
    'Permitting':   'yellow',
    'Construction': 'yellow',
    'Decommissioned': 'red'
}

platforms_icons = {
    'Fixed Surface Buoy':         'buoy',
    'Fixed Bottom Station':       'circ',
    'Fixed Bottom Mount Mooring': 'tri',
    'Fixed Coastal Station':      'shore_station',
}

url = ("https://raw.githubusercontent.com/secoora/"
       "static_assets/master/icons/")
icon = (url + "{platform}-{status}.png").format


def main():

    csv_file = 'https://docs.google.com/spreadsheets/d/1ECXoa43uq9Gr8REZF-7EGlxNa1mkP7-4YturX0nFK7s/pub?output=csv'
    df = pd.read_csv(csv_file)

    # Add computed columns
    df['status_color'] = df['Status'].map(lambda x: status_colors[x])
    df['platform_icon'] = df['PlatformType'].map(lambda x: platforms_icons[x])
    df['popupContent'] = df['LocationDescription']
    df['icon'] = df.apply(
        lambda x: icon(platform=x['platform_icon'], status=x['status_color']),
        axis=1
    )

    save_geojson(df)
    save_shapefile(df)


def save_geojson(df):
    features = []
    for r, s in df.iterrows():
        features.append(geojson.Feature(
            geometry=geojson.Point([s["Longitude"],
                                    s["Latitude"]]),
            properties={ k.lower(): v for (k, v) in s.iteritems() }
        ))

    fc = geojson.FeatureCollection(features)
    with open('stations.geojson', 'w') as f:
        geojson.dump(fc, f, sort_keys=True, indent=2, separators=(",", ": "))


def save_shapefile(df):

    def shape_name(name):
        return name.lower()[:10]

    def columns_to_properties(frame):
        props = {}
        for i, x in enumerate(df.dtypes):
            if x == object:
                props[shape_name(df.columns[i])] = 'str'
            elif x in [np.int32, np.int64]:
                props[df.columns[i][:10].lower()] = 'int'
            elif x in [np.float32, np.float64]:
                props[shape_name(df.columns[i])] = 'float'
            else:
                logger.warning('Could not find shapefile column type for {}'.format(x))
        return props

    schema = {
        'geometry': 'Point',
        'properties': columns_to_properties(df)
    }

    with fiona.open('stations.shp', "w", "ESRI Shapefile", schema) as f:
        for r, s in df.iterrows():
            f.write({
                "geometry": geojson.Point([s["Longitude"], s["Latitude"]]),
                "properties": { shape_name(k): v for (k, v) in s.iteritems() if shape_name(k) in schema['properties'] }
            })

if __name__ == "__main__":
    main()
