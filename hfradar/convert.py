#!/usr/bin/env python
# coding=utf-8

# conda execute
# env:
#  - fiona
#  - geojson
#  - pandas
#  - pygc
# channels:
#  - ioos
# run_with: python

"""
Create GeoJSON Features for SECOORA HFRadar Sites.

To test the features copy-and-paste the GeoJSON file onto:

http://geojson.io/

Run with,
$ conda execute -v convert.py

"""

import fiona
import geojson
import numpy as np
import pandas as pd
from pygc import great_circle

import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

status_colors = {
    'Planned':      'orange',
    'Operational':  'green',
    'Permitting':   'yellow',
    'Construction': 'yellow'
}

url = ("https://raw.githubusercontent.com/secoora/"
       "static_assets/master/icons/")
icon = (url + "hfradar-{status}.png").format

# The values are from a GMT script @vembus provided to @ocefpaf and @kwilcox
# The comments values were provided to @vembus to @kwilcox separately.
ranges = {
    5: 190,   # 225
    8: 160,   # 175
    12: 130,  # 124
    16: 100   # 100
}


def math_angle_to_azimuth(angle):
    return normalize_angle((360 - angle) + 90)


def normalize_angle(angle):
    return angle % 360


def wedge(distance, angle, theta, lat, lon, arc_points=None):

    try:
        arc_points = float(arc_points)
    except TypeError:
        arc_points = 50.

    pts = [[lon, lat]]

    starting = great_circle(distance=distance, azimuth=math_angle_to_azimuth(angle), latitude=lat, longitude=lon)
    pts.append([starting['longitude'], starting['latitude']])

    ending = great_circle(distance=distance, azimuth=math_angle_to_azimuth(angle+theta), latitude=lat, longitude=lon)

    # Calculate N points along the circumference between the starting and ending
    alpha = theta / arc_points
    for j in range(int(arc_points)):
        beta = alpha * j
        pt = great_circle(distance=distance, azimuth=math_angle_to_azimuth(angle+beta), latitude=lat, longitude=lon)
        pts.append([pt['longitude'], pt['latitude']])

    # Add the end point
    pts.append([ending['longitude'], ending['latitude']])

    # Add the station point
    pts.append([lon, lat])

    return geojson.Polygon([pts])


def main():

    csv_file = 'https://docs.google.com/spreadsheets/d/11hWfIr4lrKP-RviEwSio6dZgnm0oUFUII9WChPDzeAw/pub?output=csv'
    df = pd.read_csv(csv_file)

    # Add computed columns
    df['range'] = df['MHz'].map(lambda x: ranges.get(int(x), 0) * 1000)
    df['status_color'] = df['Status'].map(lambda x: status_colors[x])
    df['icon'] = df.apply(
        lambda x: icon(status=x['status_color']),
        axis=1
    )
    df['popupContent'] = df.apply(
        lambda x: '{} ({} MHz)'.format(x['DisplayTitle'], x['MHz']),
        axis=1
    )

    save_geojson(df)
    save_shapefile(df)


def save_geojson(df):
    features = []

    for r, s in df.iterrows():

        lat = s['Latitude']
        lon = s['Longitude']
        dis = s['range']
        angle = s['StartAngle']
        theta = s['SpreadAngle']

        x = s.fillna(0).copy()
        feature = geojson.Feature(
            geometry=geojson.Point([lon, lat]),
            properties={ k.lower(): v for (k, v) in x.iteritems() }
        )

        features.append(feature)

        if not pd.isnull(angle) and not pd.isnull(theta):
            x = s.fillna(0).copy()
            feature = geojson.Feature(
                geometry=wedge(dis, angle, theta, lat, lon),
                properties={ k.lower(): v for (k, v) in x.iteritems() }
            )

        features.append(feature)

    fc = geojson.FeatureCollection(features)
    with open('hfradar.geojson', 'w') as f:
        geojson.dump(fc, f, sort_keys=True, indent=2, separators=(",", ": "))


def save_shapefile(df):

    def shape_name(name):
        return name.lower()[:10]

    def columns_to_properties(frame):
        props = {}
        for i, x in enumerate(df.dtypes):
            if x == object:
                props[df.columns[i][:10].lower()] = 'str'
            elif x in [np.int32, np.int64]:
                props[df.columns[i][:10].lower()] = 'int'
            elif x in [np.float32, np.float64]:
                props[df.columns[i][:10].lower()] = 'float'
            else:
                logger.warning('Could not find shapefile column type for {}'.format(x))
        return props

    schema = {
        'geometry': 'Polygon',
        'properties': columns_to_properties(df)
    }

    with fiona.open('hfradar.shp', "w", "ESRI Shapefile", schema) as f:
        for r, s in df.iterrows():

            lat = s['Latitude']
            lon = s['Longitude']
            dis = s['range']
            angle = s['StartAngle']
            theta = s['SpreadAngle']

            if not pd.isnull(angle) and not pd.isnull(theta):
                x = s.fillna(0).copy()
                f.write({
                    "geometry": wedge(dis, angle, theta, lat, lon),
                    "properties": { shape_name(k): v for (k, v) in x.iteritems() if shape_name(k) in schema['properties'] }
                })
            else:
                x = s.fillna(0).copy()
                f.write({
                    "geometry": geojson.Polygon([[[lon, lat]] * 4 ]),
                    "properties": { shape_name(k): v for (k, v) in x.iteritems() if shape_name(k) in schema['properties'] }
                })

if __name__ == "__main__":
    main()
