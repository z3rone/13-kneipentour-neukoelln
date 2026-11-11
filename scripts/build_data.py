#!/usr/bin/env python3
"""Build geocoded GeoJSON and CSV files for uMap from input bar data."""

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

DARK_RED_BARS = {
    "zur molle (dart- und billardkneipe)",
    "blauer affe 1",
    "bierlokal zum umsteiger",
    "warthe-eck",
    "bierbaum 2",
    "zur pinte",
    "weserkrug",
    "lenau-stuben",
}

RED_BARS = {
    "bierbaum 3",
    "bechereck",
    "mahlower klause",
    "bäreneck",
    "alt-berliner bierlokal bienenkorb",
    "bierbaum 1",
    "rixdorfer",
    "astra stube neukölln",
    "zum magendoktor",
}

YELLOW_BARS = {
    "kneipe zum heinzelmann",
    "marktbörse",
    "ringbar",
    "keglerheim",
    "sandmann",
    "deriva -neukölln-",
    "loreley bar",
    "frollein langner",
    "savo bar café",
    "ruine bar",
    "sux",
    "b-lage",
    "schankwirtschaft laidak",
    "ä",
    "tristeza",
    "kollektiv bar kleinod",
}

SELECTED_BARS = [
    "Keglerheim",
    "B-Lage",
    "Zum Magendoktor",
    "Rotbart",
    "Kneipe Zum Heinzelmann",
    "Bierbaum 1",
    "Flaschenzug Bar",
    "Bierlokal Zum Umsteiger",
    "Ruine Bar",
    "Alt-Berliner Bierlokal Bienenkorb",
    "Warthe-Eck",
    "Tante Frizzante Event-Bar & KiezGarten Zart Daneben",
    "Frollein Langner",
    "bechereck",
    "Zur Molle (Dart- und Billardkneipe)",
    "Bierbaum 3",
    "Froschkönig",
    "Daffke",
    "Keith Bar",
    "Blauer Affe 1",
    "Mahlower Klause",
    "Bäreneck",
    "Schankwirtschaft Laidak",
    "Deriva -Neukölln-",
    "Sandmann",
    "Zur Pinte",
    "Bierbaum 2",
    "Rixdorfer",
    "Weser 58",
    "Ä",
    "Tristeza",
    "Weserkrug",
    "Vettern Bar",
    "Schillingbar",
    "Dschungel",
    "Lenau-Stuben",
    "Damensalon",
]
SELECTED_BARS_SET = {b.lower() for b in SELECTED_BARS}

COLOR_DARK_RED = "DarkRed"
COLOR_RED = "Red"
COLOR_YELLOW = "Yellow"
COLOR_DEFAULT = "DodgerBlue"


def geocode_address(address: str) -> tuple[float, float]:
    """Geocode address using Photon API with fallback to Nominatim."""
    cleaned_address = re.sub(r"-Bezirk\s+[A-Za-zäöüÄÖÜß]+", "", address).strip()

    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode(
        {"q": f"{cleaned_address}, Germany", "limit": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "NeukoellnKneipenMap/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("features"):
                coords = data["features"][0]["geometry"]["coordinates"]
                return float(coords[1]), float(coords[0])
    except Exception:
        pass

    time.sleep(1.0)
    nom_url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": cleaned_address, "format": "json", "limit": 1}
    )
    nom_req = urllib.request.Request(
        nom_url, headers={"User-Agent": "NeukoellnKneipenMap/1.0"}
    )
    with urllib.request.urlopen(nom_req, timeout=5) as resp:
        nom_data = json.loads(resp.read().decode())
        if nom_data:
            return float(nom_data[0]["lat"]), float(nom_data[0]["lon"])

    raise RuntimeError(f"Failed to geocode address: {address}")


def load_cached_coordinates(csv_path: Path) -> dict[str, tuple[float, float]]:
    """Load existing address coordinates from prior CSV output if present."""
    cache = {}
    if csv_path.exists():
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                addr = row.get("address", "").strip() if row.get("address") else ""
                lat_str = row.get("latitude", "").strip() if row.get("latitude") else ""
                lon_str = row.get("longitude", "").strip() if row.get("longitude") else ""
                if addr and lat_str and lon_str:
                    try:
                        cache[addr] = (float(lat_str), float(lon_str))
                    except ValueError:
                        pass
    return cache


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / "00 Musterseiten div Perioden seite-copy.csv"
    geojson_out = base_dir / "bars.geojson"
    selected_geojson_out = base_dir / "selected_bars.geojson"
    csv_out = base_dir / "bars.csv"

    coord_cache = load_cached_coordinates(csv_out)

    features = []
    features_by_lower_name = {}
    csv_rows = []

    with open(input_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Name"].strip()
            address = row["Adresse"].strip()
            hours_from = row["Oeffnung_Von"].strip()
            hours_to = row["Oeffnung_Bis"].strip()
            price = row["Preisklasse"].strip()
            rating = row["Sterne"].strip()
            reviews = row["Anzahl_Bewertungen"].strip()
            vibe = row["Vibe"].strip()

            if address in coord_cache:
                lat, lon = coord_cache[address]
            else:
                lat, lon = geocode_address(address)
                coord_cache[address] = (lat, lon)
                time.sleep(0.05)

            name_lower = name.lower()
            if name_lower in DARK_RED_BARS:
                marker_color = COLOR_DARK_RED
                category = "Kneipentour (Dunkelrot)"
                color_group = "dark_red"
            elif name_lower in RED_BARS:
                marker_color = COLOR_RED
                category = "Kneipentour (Rot)"
                color_group = "red"
            elif name_lower in YELLOW_BARS:
                marker_color = COLOR_YELLOW
                category = "Ausgewählte Bars (Gelb)"
                color_group = "yellow"
            else:
                marker_color = COLOR_DEFAULT
                category = "Weitere Bars (Blau)"
                color_group = "blue"

            description_md = (
                f"**Kategorie**: {category}\n\n"
                f"**Adresse**: {address}\n\n"
                f"**Öffnungszeiten**: {hours_from} – {hours_to}\n\n"
                f"**Preis**: {price} | **Sterne**: {rating} ({reviews} Bewertungen)\n\n"
                f"**Vibe**: {vibe}"
            )

            properties = {
                "name": name,
                "description": description_md,
                "color": marker_color,
                "_umap_options": {
                    "color": marker_color,
                },
                "category": category,
                "color_group": color_group,
                "address": address,
                "hours_from": hours_from,
                "hours_to": hours_to,
                "price": price,
                "rating": float(rating) if rating else None,
                "reviews": int(reviews) if reviews else None,
                "vibe": vibe,
            }

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": properties,
            }
            features.append(feature)
            features_by_lower_name[name_lower] = feature

            csv_rows.append(
                {
                    "name": name,
                    "latitude": lat,
                    "longitude": lon,
                    "color": marker_color,
                    "category": category,
                    "color_group": color_group,
                    "address": address,
                    "opening_hours": f"{hours_from} - {hours_to}",
                    "price": price,
                    "rating": rating,
                    "reviews": reviews,
                    "vibe": vibe,
                    "description": description_md,
                }
            )

    geojson_payload = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(geojson_out, mode="w", encoding="utf-8") as f:
        json.dump(geojson_payload, f, ensure_ascii=False, indent=2)

    selected_features = [
        features_by_lower_name[b.lower()]
        for b in SELECTED_BARS
        if b.lower() in features_by_lower_name
    ]
    selected_geojson_payload = {
        "type": "FeatureCollection",
        "features": selected_features,
    }

    with open(selected_geojson_out, mode="w", encoding="utf-8") as f:
        json.dump(selected_geojson_payload, f, ensure_ascii=False, indent=2)

    csv_fieldnames = [
        "name",
        "latitude",
        "longitude",
        "color",
        "category",
        "color_group",
        "address",
        "opening_hours",
        "price",
        "rating",
        "reviews",
        "vibe",
        "description",
    ]
    with open(csv_out, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    dark_red_count = sum(1 for f in features if f["properties"]["color_group"] == "dark_red")
    red_count = sum(1 for f in features if f["properties"]["color_group"] == "red")
    yellow_count = sum(1 for f in features if f["properties"]["color_group"] == "yellow")
    blue_count = sum(1 for f in features if f["properties"]["color_group"] == "blue")
    print(
        f"Generated {len(features)} points: {dark_red_count} DarkRed, {red_count} Red, "
        f"{yellow_count} Yellow, {blue_count} Blue in {geojson_out.name} and {csv_out.name}"
    )
    print(
        f"Generated {len(selected_features)} points in {selected_geojson_out.name}"
    )


if __name__ == "__main__":
    main()
