"""Build a traceable destination registry from structured RAG Markdown sections.

No geocoding is performed. Only explicitly reviewed overrides supply coordinates.
Combined headings remain combined records with no artificial representative point.
"""

import json
import re
from pathlib import Path

from .travel import normalize, parse_frontmatter

# Travel grouping only, not administrative boundaries. Central includes Tây Nguyên.
REGIONS = {
    **dict.fromkeys("bac_ninh cao_bang dien_bien hai_phong ha_noi hung_yen lai_chau lang_son lao_cai ninh_binh phu_tho quang_ninh son_la thai_nguyen tuyen_quang".split(), "bac"),
    **dict.fromkeys("dak_lak da_nang gia_lai ha_tinh hue khanh_hoa lam_dong nghe_an quang_ngai quang_tri thanh_hoa".split(), "trung"),
    **dict.fromkeys("an_giang can_tho ca_mau dong_nai dong_thap tay_ninh thanh_pho_ho_chi_minh vinh_long".split(), "nam"),
}
EXACT_OVERRIDES = {"ha_noi_poi_01": "ho-guom", "quang_ninh_poi_01": "ha-long",
                   "ninh_binh_poi_01": "trang-an", "an_giang_poi_05": "phu-quoc",
                   "da_nang_poi_03": "hoi-an", "da_nang_poi_04": "my-son",
                   "hue_poi_01": "hue", "thanh_pho_ho_chi_minh_poi_02": "cu-chi",
                   "thanh_pho_ho_chi_minh_poi_03": "ben-thanh"}


def category(group):
    text = normalize(group)
    if any(term in text for term in ("di tich", "lich su", "tam linh")):
        return "history"
    if "bien" in text:
        return "beach"
    if any(term in text for term in ("canh quan", "thien nhien", "sinh thai", "nui", "hang dong")):
        return "nature"
    return "attraction"


def build_catalogue(raw_dir: Path, overrides: list[dict], locations=None):
    output = {p["id"]: {**p, "rag_ids": [], "documents": []} for p in overrides}
    report = {"files": 0, "rag_records": 0, "skipped_unstructured_sections": 0}
    for path in sorted(raw_dir.rglob("*.md")):
        metadata, text = parse_frontmatter(path.read_text(encoding="utf-8"))
        province = metadata.get("province_id")
        if not province:
            continue
        if province not in REGIONS:
            raise ValueError(f"Missing travel grouping for {province}")
        report["files"] += 1
        source_lines = {match[1]: match[2] for match in re.finditer(
            r"^- \*\*(S\d+)\*\*.*?URL:\s*(https?://\S+)", text, re.MULTILINE)}
        sections = list(re.finditer(r"^### (.+)$", text, re.MULTILINE))
        for index, heading in enumerate(sections):
            end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
            section = text[heading.end():end].split("\n## ")[0]
            identifier = re.search(r"`place_id`: `([^`]+)`", section)
            if not identifier:
                report["skipped_unstructured_sections"] += 1
                continue
            rag_id, name = identifier[1], heading[1].strip()
            if any(rag_id in p["rag_ids"] for p in output.values()):
                raise ValueError(f"Duplicate RAG place_id: {rag_id}")
            group = re.search(r"^- Nhóm:\s*([^\.\n]+)\.?\s*([^\n]*)", section, re.MULTILINE)
            description = group[2].strip() if group else name
            introduction = re.search(r"^\*\*Giới thiệu[^\n]*?\*\*\s*(.+)$", section, re.MULTILINE)
            if introduction:
                description = introduction[1].strip()
            refs = re.findall(r"S\d+", section)
            urls = list(dict.fromkeys(source_lines[ref] for ref in refs if ref in source_lines))
            urls = list(dict.fromkeys([*urls, *re.findall(
                r"\]\((https?://[^\s)<>]+)\)", section)]))
            doc = {"path": path.relative_to(raw_dir).as_posix(), "place_id": rag_id,
                   "name": name, "province_id": province,
                   "province_name": metadata.get("province_name", province),
                   "researched_on": metadata.get("researched_on"), "sources": urls}
            canonical = EXACT_OVERRIDES.get(rag_id, rag_id)
            if canonical not in output:
                output[canonical] = {
                    "id": canonical, "name": name, "region": REGIONS[province],
                    "category": category(group[1] if group else ""), "coordinates": None,
                    "description": description or name,
                    "source": urls[0] if urls else "/sources/" + doc["path"],
                    "aliases": [], "rag_ids": [], "documents": [],
                    "coordinate_status": "not_verified", "image_status": "not_verified",
                }
            place = output[canonical]
            search_names = re.search(r'^- Tên dùng tìm kiếm: (.+)$', section, re.MULTILINE)
            if search_names:
                for alias in search_names[1].rstrip('.').split(', '):
                    if normalize(alias) != normalize(place['name']) and alias not in place['aliases']:
                        place['aliases'].append(alias)
            parent = re.search(r'`parent_place_id`: `([^`]+)`', section)
            if parent:
                place['parent_place_id'] = EXACT_OVERRIDES.get(parent[1], parent[1])
            if normalize(name) != normalize(place["name"]) and name not in place["aliases"]:
                place["aliases"].append(name)
            place["rag_ids"].append(rag_id)
            place["documents"].append(doc)
            if canonical in EXACT_OVERRIDES.values():
                place["coordinate_status"] = "existing_catalogue"
                place["coordinate_source"] = place["source"]
            report["rag_records"] += 1
    records = list(output.values())
    for location in locations or []:
        place = output.get(location['id'])
        if place is None:
            raise ValueError(f"Unknown coordinate record: {location['id']}")
        lon, lat = location['coordinates']
        if not (102 <= lon <= 110 and 8 <= lat <= 24) or not location.get('coordinate_source'):
            raise ValueError(f"Invalid coordinates or missing source: {location['id']}")
        place.update({k: v for k, v in location.items() if k != 'id'})
        place['description'] += ' ' + location['coordinate_note']
    images_path = Path(__file__).with_name('catalogue_images.json')
    for record in json.loads(images_path.read_text(encoding='utf8')) if images_path.exists() else []:
        if record['id'] not in output:
            raise ValueError(f"Unknown image destination: {record['id']}")
        output[record['id']]['image'] = record['image']
        output[record['id']]['image_status'] = ('supplied_permission_required'
            if record['image'].get('rights_status') == 'permission_required' else 'reviewed_source')
    report.update(total=len(records), mapped=sum(p["coordinates"] is not None for p in records),
                  unmapped=sum(p["coordinates"] is None for p in records))
    return records, report