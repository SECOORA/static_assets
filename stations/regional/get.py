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


def main():

    csv_file = 'http://sensors.axds.co/stationsensorservice/getStationCsv?polygonbounds=1115673.0397273,-11686481.208459;1115673.0397273,-5835685.3162128;5430390.4117683,-5835685.3162128;5430390.4117683,-11686481.208459;1115673.0397273,-11686481.208459&appregion=secoora&srid=3857'
    df = pd.read_csv(csv_file)

    filtered_df = filter_stations(df)
    save_geojson(filtered_df)
    save_shapefile(filtered_df)


def filter_stations(df):

    vars_to_ignore = [
        'tide_predictions',
        'stream_flow',
        'stream_height',
        'gov.usgs.waterdata'
    ]

    for v in vars_to_ignore:
        df = df[~df.sensor.str.contains(':{}'.format(v))]
    return df


def save_geojson(df):
    features = []
    for r, s in df.iterrows():
        features.append(geojson.Feature(
            geometry=geojson.Point([s["longitude (degree)"],
                                    s["latitude (degree)"]]),
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
                "geometry": geojson.Point([s["longitude (degree)"], s["latitude (degree)"]]),
                "properties": { shape_name(k): v for (k, v) in s.iteritems() if shape_name(k) in schema['properties'] }
            })


if __name__ == "__main__":
    main()
