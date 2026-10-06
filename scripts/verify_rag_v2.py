"""Validate the imported v2 collection using the real local embedding model."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.config import Settings
from rag.pipeline import RAGPipeline


def main():
    pipeline = RAGPipeline(Settings.from_env())
    payload = pipeline._store().store.get(include=["metadatas"])
    metadata = payload["metadatas"]
    assert len(metadata) >= 209, f"Unexpected chunk count: {len(metadata)}"
    assert all(row.get("dataset_version") == "2.1" for row in metadata)
    attractions = [row for row in metadata if row.get("place_id")]
    assert len(attractions) == len({row["place_id"] for row in attractions}) == 209
    assert len({row["province_id"] for row in metadata}) == 34
    assert all(json.loads(row["source_urls"]) for row in attractions)
    checks = []
    for question, expected in (
        ("Hạ Long và Tràng An có gì?", {"quang_ninh_poi_01", "ninh_binh_poi_01"}),
        ("Hang Múa có rừng quốc gia không?", {"ninh_binh_poi_03"}),
        ("Muốn đến Bút Tháp", {"bac_ninh_poi_02_b"}),
    ):
        rows = pipeline.retrieve(question)
        actual = {row.metadata.get("place_id") for row in rows}
        assert actual == expected, (question, actual, expected)
        assert all(json.loads(row.metadata["source_urls"]) for row in rows)
        checks.append({"question": question, "place_ids": sorted(actual)})
    rows = pipeline.retrieve("Giá vé Tràng An")
    assert rows and all(row.metadata["content_kind"] == "price" for row in rows)
    scope, _ = pipeline.request_scope("Mỹ Khê có gì?")
    assert scope.clarification, "Ambiguous destination must require clarification"
    print(json.dumps({"store": str(pipeline.settings.store_dir), "chunks": len(metadata),
                      "attractions": len(attractions), "provinces": 34,
                      "checks": checks, "price_check": "passed",
                      "ambiguity_check": "passed"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()