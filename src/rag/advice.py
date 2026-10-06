"""User-facing evidence projection and grounded, intent-specific response composition."""
import json
import math
import re

from .travel import normalize


def attraction_evidence(result):
    fields = {}
    for line in result.text.splitlines():
        match = re.match(r'^\*\*(.+?)\*\*\s*(.*)$', line)
        if not match or not match[2]:
            continue
        label = normalize(match[1])
        if label.startswith('gioi thieu'):
            fields['description'] = match[2]
        elif label.startswith('diem noi bat'):
            fields['highlights'] = match[2]
        elif label.startswith('trai nghiem'):
            fields['experience'] = match[2]
        elif label.startswith('luu y'):
            fields['note'] = match[2]
        elif label.startswith('tinh trang co ngay'):
            fields['dated_notice'] = match[2]
    return {'name': result.metadata.get('section', result.metadata.get('resolved_destination', '')),
            'province': result.metadata.get('province_name', ''),
            **fields, 'sources': json.loads(result.metadata.get('source_references', '[]'))}


def introduction(results, compact=False):
    sections = []
    for result in results:
        info = attraction_evidence(result)
        lines = [f"**{info['name']}** — {info['province']}"]
        if info.get('description'):
            lines.append(info['description'])
        if info.get('highlights') and not compact:
            lines.append(info['highlights'])
        if info.get('experience'):
            lines.append('Bạn có thể ' + info['experience'][0].lower() + info['experience'][1:])
        if info.get('note') and not compact:
            lines.append(info['note'])
        if info.get('dated_notice'):
            lines.append(info['dated_notice'])
        if info['sources']:
            reference = info['sources'][0]
            lines.append(f"[Nguồn: {reference['title']}]({reference['url']})")
        sections.append('\n\n'.join(lines))
    return '\n\n'.join(sections)


def distance(a, b):
    """Straight-line separation for conservative grouping, NOT travel duration."""
    lon1, lat1 = a
    lon2, lat2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(math.radians(lon2-lon1)/2)**2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def select_itinerary(scope, results, catalogue):
    """Choose one source-described local area, not a random nationwide top-k."""
    by_rag = {rag: place for place in catalogue for rag in place.get('rag_ids', [])}
    groups = {}
    for row in results:
        area = (row.metadata.get('province_id'), row.metadata.get('local_area', ''))
        groups.setdefault(area, []).append(row)
    days = min(scope.days or 3, 14)
    preferences = set(normalize(' '.join(scope.preferences)).split())
    def priority(rows):
        interest = sum(sum(word in normalize(row.text) for word in preferences) for row in rows)
        origin = sum(normalize(scope.departure) in normalize(row.metadata.get('local_area', '') + ' ' + row.metadata.get('province_name', ''))
                     for row in rows) if scope.departure else 0
        mapped = sum(row.metadata.get('place_id') in by_rag and by_rag[row.metadata['place_id']].get('coordinates') is not None for row in rows)
        return (origin, interest, min(len(rows), days*2), mapped)
    rows = max(groups.values(), key=priority) if groups else []
    # Reject known far-apart points even inside a large merged province/area.
    selected = []
    for row in rows:
        coords = by_rag.get(row.metadata.get('place_id'), {}).get('coordinates')
        known = [by_rag.get(r.metadata.get('place_id'), {}).get('coordinates') for r in selected]
        if coords and any(c and distance(coords, c) > 80 for c in known):
            continue
        selected.append(row)
        if len(selected) >= min(days*2, 8):
            break
    # Order known locations by straight-line proximity; never label this a
    # road route. Unmapped children follow their parent; other points keep their
    # source-area order and remain explicitly unverified for access.
    remaining = list(selected)
    ordered = []
    while remaining:
        previous_coords = by_rag.get(ordered[-1].metadata.get('place_id'), {}).get('coordinates') if ordered else None
        child = next((r for r in remaining if ordered and
                      r.metadata.get('parent_place_id') == ordered[-1].metadata.get('place_id')), None)
        known = [r for r in remaining if by_rag.get(r.metadata.get('place_id'), {}).get('coordinates')]
        if child:
            chosen = child
        elif previous_coords and known:
            chosen = min(known, key=lambda r: distance(previous_coords, by_rag[r.metadata['place_id']]['coordinates']))
        else:
            chosen = remaining[0]
        ordered.append(chosen)
        remaining.remove(chosen)
    return ordered


def itinerary(scope, results):
    days = min(scope.days or 3, 14)
    nights = min(scope.nights, days) if scope.nights is not None else max(0, days-1)
    area = results[0].metadata.get('local_area', results[0].metadata.get('province_name', ''))
    province = results[0].metadata.get('province_name', '')
    label = area.replace(' trước sáp nhập', '')
    lines = [f'Mình gợi ý tuyến sơ bộ tập trung ở **{label}**, trong {days} ngày {nights} đêm. '
             'Chọn một khu vực để có nhịp đi nhẹ hơn, thay vì ghép nhiều tỉnh trong chuyến ngắn.']
    if not scope.departure:
        lines.append(f'Giả định bạn có thể đến khu vực {label} vào ngày đầu và dành ngày cuối để trở về; '
                     'nếu quãng đường từ nơi xuất phát dài, cần giảm số điểm.')
    else:
        lines.append(f'Nơi xuất phát bạn cung cấp: {scope.departure}. Chưa kiểm tra tuyến di chuyển từ đó, '
                     'nên cần điều chỉnh ngày đầu/cuối theo phương tiện thực tế.')
    # Spread attractions across days. Days without enough evidence are explicit rest buffers.
    per_day = max(1, math.ceil(len(results)/days))
    for day in range(1, days+1):
        rows = results[(day-1)*per_day:day*per_day]
        lines.append(f'**Ngày {day}**')
        if rows:
            for row in rows:
                info = attraction_evidence(row)
                lines.append(f"- **{info['name']}**: {info.get('description', '')} {info.get('experience', '')}")
                if info['sources']:
                    source = info['sources'][0]
                    lines.append(f"[Nguồn: {source['title']}]({source['url']})")
        else:
            lines.append('- Dành thời gian nghỉ và di chuyển trở về; chưa có thêm điểm cùng khu vực đủ dữ liệu để ghép.')
        if day <= nights:
            lines.append(f'Khu vực nghỉ đêm gợi ý: {label} ({province}); chọn cơ sở sau khi xác nhận vị trí và phòng trống.')
    lines.append('Đây chưa phải chuyến đi hay báo giá đã xác nhận. Thứ tự ghé là gợi ý; chưa có dịch vụ định tuyến '
                 'để kiểm tra đường đi, thời gian di chuyển hoặc lịch tàu. Cần xác nhận thời tiết, dịch vụ và phương tiện trước khi chốt.')
    omitted = [target.name for target in scope.targets if target.place_id
               and target.place_id not in {r.metadata.get('place_id') for r in results}]
    if omitted:
        lines.append('Chưa ghép ' + ', '.join(omitted) + ' vào tuyến này vì khác cụm hoặc thiếu thông tin tiếp cận; '
                     'cần kiểm tra phương tiện và thời gian trước khi bổ sung.')
    if scope.budget:
        lines.append(f'Ngân sách bạn nêu: {scope.budget}; chưa đủ báo giá theo đơn vị để tính tổng.')
    lines.append('Bạn xuất phát từ đâu và thích sông nước, biển hay lịch sử hơn?' if not scope.departure
                 else 'Bạn đi bằng phương tiện gì để mình điều chỉnh nhịp chuyến đi?')
    return '\n\n'.join(lines)


def price_answer(results):
    lines = ['Giá dưới đây chỉ là **tham khảo từ nguồn**, chưa xác nhận áp dụng cho ngày bạn đi:']
    statuses = {'published_reference': 'giá nguồn từng công bố, cần xác nhận lại',
                'historical_reference': 'giá lịch sử, không phải báo giá hiện hành',
                'unknown': 'chưa có giá đủ rõ'}
    for result in results:
        for line in result.text.splitlines():
            if not line.startswith('|') or '`' not in line:
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            cleaned = [re.sub(r'\[S\d+\]', '', cell).replace('`', '').strip() for cell in cells]
            cleaned = [statuses.get(cell, cell) for cell in cleaned if cell]
            lines.append('- ' + '; '.join(cleaned))
        date = result.metadata.get('base_prices_researched_on', result.metadata.get('researched_on', ''))
        if date:
            lines.append(f'Ngày đọc nguồn giá: {date}, không phải ngày cơ sở xác nhận báo giá.')
    lines.append('Cần kiểm tra đúng dịch vụ, đối tượng vé, đơn vị và phụ thu với nơi phục vụ trước khi đặt.')
    return '\n\n'.join(dict.fromkeys(lines))