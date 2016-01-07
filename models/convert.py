#!/usr/bin/env python
# coding=utf-8

# conda execute
# env:
#  - fiona
#  - gridgeo
#  - iris
# channels:
#  - ioos
# run_with: python

"""
Create GeoJSON Features for SECOORA Models.

To test the features copy-and-paste the GeoJSON file onto:

http://geojson.io/

Run with,
$ conda execute -v convert.py

"""

import json
import iris
import warnings
from gridgeo import GridGeo
from netCDF4 import Dataset

import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.WARNING)


def main():
    features = []
    urls = ['http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
            'SABGOM_Forecast_Model_Run_Collection_best.ncd',
            'http://crow.marine.usf.edu:8080/thredds/dodsC/FVCOM-Nowcast-Agg.nc']
    for url in urls:
        with Dataset(url) as nc:
            try:
                grid = GridGeo(nc)
            except ValueError:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    cube = iris.load_cube(url, 'sea_water_potential_temperature')
                    grid = GridGeo(cube)
            features.append({'geometry': grid.outline.__geo_interface__,
                             'type': 'Feature',
                             'properties': {'popupContent': getattr(nc, 'summary', url)}})

    fc = {'features': features, 'type': 'FeatureCollection'}
    with open('models.geojson', 'w') as f:
        f.write(json.dumps(fc, sort_keys=True,
                           indent=2, separators=(",", ": ")))

if __name__ == "__main__":
    main()
