#!/usr/bin/env python3
"""Build geocoded GeoJSON and CSV files for uMap from input bar data."""

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def geocode_address(address: str) -> tuple[float, float]:
    """Geocode address using Photon API with fallback to Nominatim."""
    url = "https://photon.komoot.io/api/?" + urllib.parse.urlencode(
        {"q": f"{address}, Germany", "limit": 1}
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
        {"q": address, "format": "json", "limit": 1}
    )
    nom_req = urllib.request.Request(
        nom_url, headers={"User-Agent": "NeukoellnKneipenMap/1.0"}
    )
    with urllib.request.urlopen(nom_req, timeout=5) as resp:
        nom_data = json.loads(resp.read().decode())
        if nom_data:
            return float(nom_data[0]["lat"]), float(nom_data[0]["lon"])

    raise RuntimeError(f"Failed to geocode address: {address}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    input_file = base_dir / "00 Musterseiten div Perioden seite-copy.csv"
    geojson_out = base_dir / "bars.geojson"
    csv_out = base_dir / "bars.csv"

    features = []
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

            lat, lon = geocode_address(address)
            time.sleep(0.05)

            description_md = (
                f"**Adresse**: {address}\n\n"
                f"**Öffnungszeiten**: {hours_from} – {hours_to}\n\n"
                f"**Preis**: {price} | **Sterne**: {rating} ({reviews} Bewertungen)\n\n"
                f"**Vibe**: {vibe}"
            )

            properties = {
                "name": name,
                "description": description_md,
                "address": address,
                "hours_from": hours_from,
                "hours_to": hours_to,
                "price": price,
                "rating": float(rating) if rating else None,
                "reviews": int(reviews) if reviews else None,
                "vibe": vibe,
            }

            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                    "properties": properties,
                }
            )

            csv_rows.append(
                {
                    "name": name,
                    "latitude": lat,
                    "longitude": lon,
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

    csv_fieldnames = [
        "name",
        "latitude",
        "longitude",
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

    print(f"Generated {len(features)} points in {geojson_out.name} and {csv_out.name}")


if __name__ == "__main__":
    main()
