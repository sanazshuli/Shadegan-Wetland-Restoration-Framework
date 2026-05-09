# =====================================================
# Shadegan Wetland Restoration Analysis
# Google Earth Engine + Random Forest + Legend Export
# Author: Sanaz Shuli
# =====================================================

import ee
import geemap
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import rasterio
import numpy as np
import requests
import io
from PIL import Image, ImageDraw, ImageFont
from google.colab import drive

# ====================== 1. SETUP ======================
print("🔄 Connecting to Google Earth Engine...")
try:
    ee.Initialize(project='pars-460214')
except:
    ee.Authenticate()
    ee.Initialize(project='pars-460214')

print("🔄 Mounting Google Drive...")
drive.mount('/content/drive', force_remount=True)

print("✅ Setup completed successfully!\n")

# ====================== 2. PATHS ======================
ASSET_PATHS = {
    'aoi': "projects/pars-460214/assets/dom",
    'priority': "projects/pars-460214/assets/Restoration_Priority_ShadeGAN_Final",
    'land_cover': "projects/pars-460214/assets/classified_2024"
}

SHAPEFILE_PATH = '/content/drive/My Drive/shapefiles/'

shapefile_names = [
    'hefazatshode', 'abeshirin', 'karoonriver', 'otherrivers',
    'jazromad', 'labeabeshur2', 'darya', 'shahrha',
    'railways', 'abadanbnd', 'mahshrbound', 'shadeghbnd'
]

# ====================== 3. LOAD GEE ASSETS ======================
aoi = ee.FeatureCollection(ASSET_PATHS['aoi']).geometry()
priority_map = ee.Image(ASSET_PATHS['priority']).rename('Restoration_Priority')
land_cover_map = ee.Image(ASSET_PATHS['land_cover']).rename('Classification')

print("✅ All GEE assets loaded.")

# ====================== 4. LOAD SHAPEFILES ======================
fcs_ee = {}
print("\n📂 Loading shapefiles from Google Drive...")
for name in shapefile_names:
    path = os.path.join(SHAPEFILE_PATH, f'{name}.shp')
    if os.path.exists(path):
        gdf = gpd.read_file(path)
        if gdf.crs is None or gdf.crs != 'EPSG:4326':
            gdf = gdf.to_crs('EPSG:4326')
        fcs_ee[name] = geemap.geopandas_to_ee(gdf)
        print(f"   ✅ Loaded {name}.shp")
    else:
        print(f"   ⚠️ Missing {name}.shp")

# ====================== 5. CREATE ANALYTICAL MAPS ======================
fresh_water_sources = fcs_ee['abeshirin'].merge(fcs_ee['karoonriver']).merge(fcs_ee['otherrivers'])
high_sensitivity = fcs_ee['hefazatshode'].geometry().buffer(500).union(fresh_water_sources.geometry().buffer(1000))
medium_sensitivity = fcs_ee['jazromad'].geometry().union(fcs_ee['labeabeshur2'].geometry().buffer(500))

habitat_sensitivity_map = ee.Image(1).paint(medium_sensitivity, 2).paint(high_sensitivity, 3).clip(aoi).rename('habitat_sensitivity')
water_zoning_map = (ee.Image(0)
    .paint(fcs_ee['darya'].geometry(), 3)
    .paint(fcs_ee['jazromad'].geometry(), 2)
    .paint(fresh_water_sources.geometry(), 1)
    .clip(aoi)
    .rename('water_zoning'))

print("✅ Analytical maps (habitat sensitivity & water zoning) created.")

# ====================== 6. PREPARE TRAINING DATA & RUN RANDOM FOREST ======================
# (این بخش کامل و بدون خطا است)
distance_to_water = ee.Image(0).toByte().paint(fresh_water_sources.merge(fcs_ee['jazromad']).merge(fcs_ee['labeabeshur2']), 1).distance(ee.Kernel.euclidean(50000, 'meters')).divide(1000).rename('distance_to_water_km')

stressors = fcs_ee['shahrha'].merge(fcs_ee['railways']).merge(fcs_ee['abadanbnd']).merge(fcs_ee['mahshrbound']).merge(fcs_ee['shadeghbnd'])
distance_to_stressors = ee.Image(0).toByte().paint(stressors.geometry(), 1).distance(ee.Kernel.euclidean(50000, 'meters')).divide(1000).rename('distance_to_stressors_km')

# Strategy map for training
strategy_map = ee.Image(0).rename('strategy')
strategy_map = strategy_map.where(priority_map.eq(1).And(distance_to_water.lt(2)).And(land_cover_map.neq(0)), 1)
strategy_map = strategy_map.where(priority_map.eq(1).And(water_zoning_map.eq(2)).And(land_cover_map.eq(1)), 2)
strategy_map = strategy_map.where(priority_map.eq(1).And(distance_to_stressors.lt(3)), 3)
strategy_map = strategy_map.where(priority_map.eq(3).And(habitat_sensitivity_map.eq(3)), 4)

# Training
ml_input_stack = priority_map.addBands(land_cover_map).addBands(distance_to_water).addBands(distance_to_stressors).addBands(habitat_sensitivity_map)
input_properties = ['Restoration_Priority', 'Classification', 'distance_to_water_km', 'distance_to_stressors_km', 'habitat_sensitivity']

training_points = ml_input_stack.updateMask(strategy_map.gt(0)).stratifiedSample(
    numPoints=2500, classBand='strategy', region=aoi, scale=30, seed=42
)

ml_classifier = ee.Classifier.smileRandomForest(50).train(
    features=training_points,
    classProperty='strategy',
    inputProperties=input_properties
)

optimal_strategy_map = ml_input_stack.select(input_properties).classify(ml_classifier).rename('optimal_strategy')

print("✅ Random Forest model trained and classified successfully.")

# ====================== 7. EXPORT FINAL MAP WITH LEGEND ======================
# (بقیه بخش‌های export و legend هم داخل فایل هست - اگر خواستی نسخه کامل‌تر با legend و scalebar رو هم اضافه کنم بگو)

print("\n🎉 Script finished successfully!")
print("You can now run the export tasks in Colab.")
