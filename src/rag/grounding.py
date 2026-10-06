"""Resolve requests against source sections, never against generated recommendations."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .travel import normalize, resolve_provinces


def contains(text, name):
    return bool(name) and f" {normalize(name)} " in f" {normalize(text)} "


def content_kind(metadata, text):
    section = normalize(metadata.get("section", ""))
    if metadata.get("place_id"):
        return "attraction"
    if "luu tru" in section or "homestay" in section or "khach san" in section:
        return "accommodation"
    if "gia tham khao" in section:
        return "price"
    if "quan an" in section or "nha hang" in section:
        return "food"
    return "general"


@dataclass(frozen=True)
class Target:
    name: str
    province_id: str
    place_id: str = ""
    business: str = ""


@dataclass
class RequestScope:
    question: str
    intent: str
    targets: list[Target]
    clarification: str = ""
    region: str = ""
    days: int | None = None
    nights: int | None = None
    departure: str = ""
    budget: str = ""
    preferences: list[str] = field(default_factory=list)


def intent_for(question):
    q = normalize(question)
    if any(contains(q, word) for word in ("lịch trình", "hành trình", "kế hoạch", "trip plan", "chuyến đi")) or re.search(r'\d+\s*(ngay|dem)', q):
        return "itinerary"
    if any(contains(q, word) for word in ("so sánh", "khác nhau", "hay hơn", "nên chọn")):
        return "comparison"
    price_query = q.replace('quoc gia', 'quoc')
    if any(contains(price_query, word) for word in ("giá", "vé", "chi phí", "bao nhiêu")):
        return "price"
    if any(contains(q, word) for word in ("khách sạn", "homestay", "lưu trú", "nhà nghỉ", "hotel")):
        return "accommodation"
    if any(contains(q, word) for word in ("hoạt động", "làm gì", "chơi gì", "trải nghiệm")):
        return "activities"
    if any(contains(q, word) for word in ("ăn gì", "món ăn", "ăn uống", "nhà hàng", "quán ăn")):
        return "food"
    return "introduction"


def resolve_request(question, history, documents):
    catalogue_path = Path(__file__).with_name("catalogue.json")
    catalogue = json.loads(catalogue_path.read_text(encoding="utf-8"))
    pois = {d.metadata["place_id"]: d for d in documents if d.metadata.get("place_id")}

    def identify(text):
        candidates = []
        for identifier, doc in pois.items():
            title = doc.metadata.get("section", "")
            names = [title, *re.split(r"\s+[–—]\s+", title),
                     *json.loads(doc.metadata.get("search_names", "[]"))]
            for place in catalogue:
                if identifier in place.get("rag_ids", []):
                    names.extend([place["name"], *place.get("aliases", [])])
                # A standalone map record may refer to part of a combined source POI.
                elif normalize(place["name"]) in [normalize(n) for n in names]:
                    names.extend([place["name"], *place.get("aliases", [])])
            # Province aliases are scopes, not extra POI recommendations.
            province_names = [doc.metadata.get("province_name", ""),
                              *json.loads(doc.metadata.get("aliases", "[]"))]
            matched = [n for n in names if contains(text, n)
                       and normalize(n) not in {normalize(p) for p in province_names}]
            if matched:
                name = max(matched, key=lambda n: len(normalize(n)))
                name = next((n for n in names if normalize(n) == normalize(name)
                             and n != normalize(n)), name)
                if normalize(name) == 'ha long' and normalize(title) == 'vinh ha long':
                    name = title
                candidates.append(Target(name, doc.metadata["province_id"], identifier))
        for doc in documents:
            if content_kind(doc.metadata, doc.page_content) not in {"accommodation", "food"}:
                continue
            for line in doc.page_content.splitlines():
                if not line.startswith("- ") or " — " not in line:
                    continue
                for name in line[2:].split(" — ")[0].split(", "):
                    if name and contains(text, name):
                        candidates.append(Target(name, doc.metadata["province_id"], business=name))
        # Longer nested names win; repeated sections cannot duplicate destinations.
        unique = list(dict.fromkeys(candidates))
        unique = [t for t in unique if not any(t != other and contains(other.name, t.name)
                  and normalize(other.name) != normalize(t.name) for other in unique)]
        provinces = resolve_provinces(text, [d.metadata for d in documents])
        if not provinces:
            duplicate = any(len({t.province_id for t in unique if normalize(t.name) == name}) > 1
                            for name in {normalize(t.name) for t in unique})
            if duplicate:
                for message in reversed(history or []):
                    if message.get('role') != 'user':
                        continue
                    provinces = resolve_provinces(message['text'], [d.metadata for d in documents])
                    if provinces:
                        break
        for name in {normalize(t.name) for t in unique}:
            same = [t for t in unique if normalize(t.name) == name]
            if len({t.province_id for t in same}) > 1:
                qualified = [t for t in same if t.province_id in provinces]
                if len(qualified) != 1:
                    return [], f"Bạn muốn hỏi {same[0].name} ở tỉnh nào?"
                unique = [t for t in unique if t not in same] + qualified
        if not unique:
            for province in provinces:
                doc = next(d for d in documents if d.metadata.get("province_id") == province)
                unique.append(Target(doc.metadata["province_name"], province))
        unique.sort(key=lambda t: normalize(text).find(normalize(t.name)))
        return unique, ""

    targets, clarification = identify(question)
    intent = intent_for(question)
    contextual = question
    from .catalogue_builder import REGIONS
    region = next((key for name, key in [('miền Bắc', 'bac'), ('miền Trung', 'trung'),
                  ('miền Nam', 'nam'), ('miền Tây', 'nam'), ('Tây Nguyên', 'trung')]
                   if contains(question, name)), '')
    if region and not targets:
        for province in sorted({d.metadata.get('province_id') for d in documents
                                if REGIONS.get(d.metadata.get('province_id')) == region}):
            doc = next(d for d in documents if d.metadata.get('province_id') == province)
            targets.append(Target(doc.metadata['province_name'], province))
    day = re.search(r'(\d+)\s*ngay', normalize(question))
    night = re.search(r'(\d+)\s*dem', normalize(question))
    days, nights = int(day[1]) if day else None, int(night[1]) if night else None
    departure_match = re.search(r'(?:xuất phát|khởi hành|bắt đầu|xuat phat|khoi hanh|bat dau)\s*(?:từ|ở|tu|o)?\s*([^,;?.]+)', question, re.I)
    departure = departure_match[1].strip() if departure_match else ''
    budget_match = re.search(r'(\d+(?:[.,]\d+)?\s*(?:triệu|trieu|tr|VND|đồng|dong))', question, re.I)
    preferences = [name for name in ('biển', 'sông nước', 'miệt vườn', 'lịch sử', 'thiên nhiên', 'ẩm thực', 'nghỉ dưỡng') if contains(question, name)]
    # Departure is not an additional destination when a region/province was supplied.
    if departure and (region or len(targets) > 1):
        without_origin, _ = identify(question.replace(departure_match[0], ''))
        if without_origin:
            targets = without_origin
        elif region:
            targets = list(dict.fromkeys(Target(d.metadata['province_name'], d.metadata['province_id'])
                        for d in documents if REGIONS.get(d.metadata.get('province_id')) == region))
    continuation = any(contains(question, term) for term in
            ('ở đó', 'nơi đó', 'chỗ đó', 'địa điểm này', 'điểm này', 'còn ở đó',
             'còn giá', 'đi tiếp', 'thêm một ngày', 'thích', 'ngân sách', 'xuất phát', 'khởi hành'))
    if not targets and not clarification and (continuation or days or nights):
        # Only user-authored scope establishes context; assistant text is not evidence.
        for item in reversed(history or []):
            if item.get("role") != "user":
                continue
            targets, clarification = identify(item["text"])
            if targets or clarification:
                previous_day = re.search(r'(\d+)\s*ngay', normalize(item['text']))
                previous_night = re.search(r'(\d+)\s*dem', normalize(item['text']))
                if continuation and intent_for(item['text']) == 'itinerary':
                    intent = 'itinerary'
                    days = days or (int(previous_day[1]) if previous_day else None)
                    nights = nights if nights is not None else (int(previous_night[1]) if previous_night else None)
                if len(targets) > 1 and intent != 'itinerary':
                    clarification = "Bạn muốn hỏi tiếp về " + " hay ".join(t.name for t in targets) + "?"
                contextual += "\nĐịa điểm đang trao đổi: " + ", ".join(t.name for t in targets)
                break
            previous_region = next((key for name, key in [('miền Bắc', 'bac'), ('miền Trung', 'trung'), ('miền Nam', 'nam')]
                                    if contains(item['text'], name)), '')
            if previous_region:
                region = previous_region
                targets = [Target(d.metadata['province_name'], d.metadata['province_id'])
                           for d in documents if REGIONS.get(d.metadata.get('province_id')) == region]
                targets = list(dict.fromkeys(targets))
                previous_day = re.search(r'(\d+)\s*ngay', normalize(item['text']))
                previous_night = re.search(r'(\d+)\s*dem', normalize(item['text']))
                days = days or (int(previous_day[1]) if previous_day else None)
                nights = nights if nights is not None else (int(previous_night[1]) if previous_night else None)
                intent = 'itinerary'
                break
    if targets and intent == "introduction":
        # A bare list can continue an explicit hotel/itinerary request, but not a stale topic.
        bare = normalize(question)
        for t in targets:
            bare = bare.replace(normalize(t.name), " ")
        if not set(bare.split()) - {"va", "voi", "vinh"}:
            previous = next((h["text"] for h in reversed(history or []) if h.get("role") == "user"), "")
            if not identify(previous)[0] and intent_for(previous) in {"accommodation", "itinerary"}:
                intent = intent_for(previous)
    if any(t.business for t in targets) and intent == "introduction":
        intent = "business"
    if intent == 'introduction' and (region or any(not t.place_id and not t.business for t in targets)):
        intent = 'discovery'
    if (days is not None and not 1 <= days <= 14) or (nights is not None and (nights < 0 or nights > (days or 14))):
        clarification = 'Mình hỗ trợ tuyến sơ bộ 1–14 ngày. Bạn cho biết số ngày và số đêm phù hợp nhé.'
    return RequestScope(contextual, intent, targets, clarification, region, days, nights,
                        departure, budget_match[1] if budget_match else '', preferences)


def allowed_document(doc, target, intent):
    if doc.metadata.get("province_id") != target.province_id:
        return False
    kind = content_kind(doc.metadata, doc.page_content)
    if target.business:
        return kind in {"accommodation", "food", "price"} and contains(doc.page_content, target.business)
    if intent in {"introduction", "activities", "comparison", "discovery", "itinerary"}:
        return kind == "attraction" and (not target.place_id or doc.metadata.get("place_id") == target.place_id)
    if intent == "accommodation":
        return kind == "accommodation"
    if intent == "food":
        return kind == "food"
    if intent == "price":
        return kind == "price" and (not target.place_id or contains(doc.page_content, target.name))
    return kind in {"attraction", "accommodation", "price"} and (
        kind != "attraction" or not target.place_id or doc.metadata.get("place_id") == target.place_id)


def introduction_excerpt(name, results):
    """Sparse source data must not be expanded into invented experiences."""
    lines = []
    for result in results:
        expanded = []
        for line in result.text.splitlines():
            if line.startswith(("**Giới thiệu", "**Điểm nổi bật:",
                                "**Trải nghiệm gợi ý:", "**Lưu ý riêng:")):
                expanded.append(line.split("**", 2)[-1].strip())
        if expanded:
            lines.extend(expanded)
            continue
        for line in result.text.splitlines():
            if line.startswith("- Nhóm:"):
                # The first sentence is an internal category, not travel prose.
                value = line.removeprefix("- Nhóm:").strip()
                _, separator, description = value.partition('. ')
                if separator and description.strip():
                    lines.append(description.strip())
    detail = " ".join(dict.fromkeys(lines))
    if not detail:
        detail = "Mình chưa có thông tin đủ rõ để giới thiệu điểm này."
    urls = list(dict.fromkeys(url for result in results
                             for url in json.loads(result.metadata.get('source_urls', '[]'))))
    if urls:
        detail += "\nNguồn: " + ", ".join(urls)
    province = next((r.metadata.get('province_name') for r in results if r.metadata.get('province_name')), '')
    heading = name + (f" — {province}" if province else "")
    return f"{heading}\n{detail}"