# 13 Kneipentour Neukölln

Geocoded dataset of bars and pubs in Berlin-Neukölln.

## Files

- [bars.geojson](file:///Users/falk/workspaces/misc/13-kneipen-neukoelln/bars.geojson): GeoJSON FeatureCollection formatted for GIS and web maps (uMap, Leaflet, MapLibre).
- [bars.csv](file:///Users/falk/workspaces/misc/13-kneipen-neukoelln/bars.csv): CSV file containing `name`, `latitude`, `longitude`, opening hours, ratings, and vibes.
- [scripts/build_data.py](file:///Users/falk/workspaces/misc/13-kneipen-neukoelln/scripts/build_data.py): Geocoding script converting the source CSV to GeoJSON and CSV with coordinates.

## Using as Remote Data Source in uMap

1. In uMap, open the layer settings panel (gear icon on your layer).
2. Expand **Remote data** (Erweiterte Aktionen / Externe Daten).
3. In the **Url** field, paste:
   ```
   https://raw.githubusercontent.com/z3rone/13-kneipentour-neukoelln/main/bars.geojson
   ```
4. Set **Format** to `geojson`.
5. Enable **Dynamic** (Dynamisch) if you want the map to reload the latest version on each load.
6. Click **Save** (Speichern).

