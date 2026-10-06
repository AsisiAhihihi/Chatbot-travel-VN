"""Regenerate shared map records without modifying the Chroma index."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.catalogue_builder import build_catalogue

if __name__ == "__main__":
    directory = ROOT / "src" / "rag"
    overrides = json.loads((directory / "catalogue_overrides.json").read_text(encoding="utf-8"))
    locations_path = directory / 'catalogue_locations.json'
    locations = json.loads(locations_path.read_text(encoding='utf8')) if locations_path.exists() else []
    records, report = build_catalogue(ROOT / "data" / "raw", overrides, locations)
    for filename, data in (("catalogue.json", records), ("catalogue_report.json", report)):
        (directory / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    public = ROOT / 'frontend' / 'public' / 'data'
    public.mkdir(parents=True, exist_ok=True)
    keys = ('id', 'name', 'region', 'category', 'coordinates', 'description', 'duration',
            'image', 'source', 'aliases', 'coordinate_source', 'coordinate_note',
            'resolved_name', 'map_usage', 'coordinate_type', 'navigation_ready')
    public.joinpath('places.json').write_text(json.dumps([
        {key: place[key] for key in keys if key in place} for place in records
    ], ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf8')
    print(json.dumps(report))