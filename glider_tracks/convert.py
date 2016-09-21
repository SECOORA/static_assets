#!/usr/bin/env python
# coding=utf-8

# conda execute
# env:
#  - fiona
# channels:
#  - conda-forge
# run_with: python

"""
Create GeoJSON Features for SECOORA Glider Tracks.

To test the features copy-and-paste the GeoJSON file onto:

http://geojson.io/

Run with,
$ conda execute -v convert.py

"""

import json
import fiona

import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)


def main():
    features = []
    with fiona.open('georef_glider_triangles.shp') as shp:
        for k, item in shp.items():
            features.append(item)

    fc = {'features': features, 'type': 'FeatureCollection'}
    with open('georef_glider_triangles.geojson', 'w') as f:
        f.write(json.dumps(fc, sort_keys=True,
                           indent=2, separators=(",", ": ")))

    features = []
    with fiona.open('gliders_from_georefd.shp') as shp:
        for k, item in shp.items():
            features.append(item)

    fc = {'features': features, 'type': 'FeatureCollection'}
    with open('gliders_from_georefd.geojson', 'w') as f:
        f.write(json.dumps(fc, sort_keys=True,
                           indent=2, separators=(",", ": ")))

if __name__ == "__main__":
    main()
