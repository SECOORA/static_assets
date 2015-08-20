#!python
# coding=utf-8

import os
import csv
import glob
import subprocess
from pygc import great_circle
from geojson import Feature, Polygon, FeatureCollection


mhz_to_dist = {
    5:    225,
    8.3:  175,
    12.6: 125,
    16:   100,
}


def math_angle_to_azimuth(angle):
    return normalize_angle((360 - angle) + 90)


def normalize_angle(angle):
    return angle % 360


def main():
    with open('./hfradar.csv', 'rb') as csvfile:

        feats = []
        for i, row in enumerate(csv.DictReader(csvfile)):
            mhz = float(row['MHz'])
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            dis = mhz_to_dist.get(mhz, 0) * 1000
            try:
                angle = float(row['StartAngle'])
                theta = float(row['SpreadAngle'])
            except ValueError:
                continue

            # Start with the station point
            pts = [[lon, lat]]

            starting = great_circle(distance=dis, azimuth=math_angle_to_azimuth(angle), latitude=lat, longitude=lon)
            pts.append([starting['longitude'], starting['latitude']])

            ending = great_circle(distance=dis, azimuth=math_angle_to_azimuth(angle+theta), latitude=lat, longitude=lon)

            # Calculate N points along the circumference between the starting and ending
            n = 50.
            alpha = theta / n
            for j in range(int(n)):
                beta = alpha * j
                pt = great_circle(distance=dis, azimuth=math_angle_to_azimuth(angle+beta), latitude=lat, longitude=lon)
                pts.append([pt['longitude'], pt['latitude']])

            # Add the end point
            pts.append([ending['longitude'], ending['latitude']])

            # Add the station point
            pts.append([lon, lat])

            feats.append(Feature(geometry=Polygon([pts]), id=i, properties=row))

    with open("hfradar.geojson", 'w') as f:
        f.write(str(FeatureCollection(feats)))

    for f in glob.glob('./hfradar_coverage*'):
        os.remove(f)

    subprocess.call(['ogr2ogr', 'hfradar_coverage.shp', 'hfradar.geojson'])

main()
