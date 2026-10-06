"""Province metadata, structured travel chunks and accent-insensitive lookup."""

import json
import re
import unicodedata

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import yaml


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", "".join(
        char for char in text if not unicodedata.combining(char)
    )).split())


def parse_frontmatter(text: str):
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Markdown frontmatter must be a mapping")
    metadata = {}
    for key, value in data.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            value = str(value)
        if value is not None:
            metadata[key] = value
    return metadata, text[match.end():].strip()


def split_travel_document(document: Document, chunk_size: int, overlap: int):
    """Keep each POI intact; split large price tables only between full rows."""
    text = document.page_content
    source_lines = {}
    for line in text.splitlines():
        match = re.match(r"- \*\*(S\d+)\*\*", line)
        if match:
            source_lines[match.group(1)] = line
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
    boundaries = list(re.finditer(r"^#{2,3} .+$", text, re.MULTILINE))
    chunks = []
    for index, heading in enumerate(boundaries):
        end = boundaries[index + 1].start() if index + 1 < len(boundaries) else len(text)
        section = text[heading.start():end].strip()
        title = heading.group().lstrip("# ")
        if not section[len(heading.group()):].strip():
            continue
        if title in {"Nguồn và thời điểm", "Quy tắc trả lời và dữ liệu bản đồ"}:
            continue
        if "`place_id`" in section:
            parts = [section]
        elif "|---" in section:
            lines = section.splitlines()
            table_start = next(i for i, line in enumerate(lines) if line.startswith("|"))
            prefix = "\n".join(lines[:table_start + 2])
            rows = [line for line in lines[table_start + 2:] if line.startswith("|")]
            parts, current = [], prefix
            for row in rows:
                if len(current) + len(row) + 1 > chunk_size and current != prefix:
                    parts.append(current)
                    current = prefix
                current += "\n" + row
            if current != prefix:
                parts.append(current)
        else:
            parts = splitter.split_text(section)
        for part in parts:
            refs = set(re.findall(r"S\d+", part))
            sources = "\n".join(source_lines[ref] for ref in source_lines if ref in refs)
            description_sources = "\n".join(
                line for line in part.splitlines()
                if line.startswith("- [") and "https://" in line
            )
            sources = "\n".join(value for value in (sources, description_sources) if value)
            metadata = {**document.metadata, "section": title,
                        "start_index": heading.start(), "source_details": sources,
                        "source_urls": json.dumps(list(dict.fromkeys(
                            re.findall(r"https?://[^\s)<>]+", sources))), ensure_ascii=False)}
            from .catalogue_builder import REGIONS
            metadata['region'] = REGIONS.get(metadata.get('province_id'), '')
            place = re.search(r"`place_id`: `([^`]+)`", part)
            if place:
                metadata["place_id"] = place.group(1)
            for field in ("parent_place_id", "legacy_group_id"):
                value = re.search(rf"`{field}`: `([^`]+)`", part)
                if value:
                    metadata[field] = value.group(1)
            area = re.search(r"^- Tỉnh/thành: .+?; khu vực: (.+)$", part, re.MULTILINE)
            if area:
                metadata['local_area'] = area.group(1).rstrip('.')
            references = [{'title': title, 'url': url} for title, url in re.findall(
                r'^- \[([^\]]+)\]\((https?://[^\s)<>]+)\)', part, re.MULTILINE)]
            for ref in source_lines:
                if ref not in refs:
                    continue
                line = source_lines[ref]
                url = re.search(r'URL:\s*(https?://\S+)', line)
                title_match = re.search(r'— (.+?)\. Ngày hiển thị', line)
                if url:
                    references.append({'title': title_match[1] if title_match else title,
                                       'url': url[1]})
            metadata['source_references'] = json.dumps(references, ensure_ascii=False)
            kind = re.search(r"`content_type`: `([^`]+)`", part)
            if kind:
                metadata["content_type"] = kind.group(1)
            elif "lưu trú" in title.lower():
                metadata["content_type"] = "accommodation"
            elif "giá tham khảo" in title.lower():
                metadata["content_type"] = "price"
            elif "quán ăn" in title.lower() or "nhà hàng" in title.lower():
                metadata["content_type"] = "food"
            else:
                metadata["content_type"] = "general"
            search_names = re.search(r"^- Tên dùng tìm kiếm: (.+)$", part, re.MULTILINE)
            if search_names:
                metadata["search_names"] = json.dumps(
                    [name.strip() for name in search_names.group(1).rstrip('.').split(',')],
                    ensure_ascii=False)
            metadata["price_status"] = json.dumps(list(dict.fromkeys(
                re.findall(r"`(historical_reference|published_reference|unknown)`", part))))
            content = (f"Tỉnh/thành: {metadata['province_name']}\n"
                       f"Ngày tra cứu dữ liệu (không phải ngày hiệu lực giá): {metadata.get('researched_on', 'chưa rõ')}\n"
                       + (f"Ngày tra cứu nguồn giá gốc (không phải báo giá hiện hành): {metadata['base_prices_researched_on']}\n"
                          if metadata.get('base_prices_researched_on') else "") +
                       f"{part}")
            chunks.append(Document(page_content=content, metadata=metadata))
    return chunks


def resolve_provinces(question: str, metadata_rows):
    question = f" {normalize(question)} "
    matches = set()
    for metadata in metadata_rows:
        province = metadata.get("province_id")
        if not province:
            continue
        aliases = json.loads(metadata.get("aliases", "[]"))
        names = [metadata.get("province_name", ""), *aliases]
        if any(name and f" {normalize(name)} " in question for name in names):
            matches.add(province)
    return sorted(matches)