"""HTTP adapter for the existing RAG; map coordinates never come from the LLM."""

import json
import logging
import os
import re
import time
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Literal
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .config import Settings
from .pipeline import RAGPipeline
from .travel import normalize

CATALOGUE = json.loads(Path(__file__).with_name("catalogue.json").read_text(encoding="utf-8"))
logger = logging.getLogger(__name__)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(max_length=12000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    history: list[Message] = Field(default_factory=list, max_length=40)


def match_places(text):
    query = f" {normalize(text)} "
    return [place for place in CATALOGUE if any(
        f" {normalize(name)} " in query for name in [place["name"], *place["aliases"]]
    )]


def ambiguous_matches(found, text):
    """Duplicate names require provincial context; never silently pick one."""
    query = f" {normalize(text)} "
    selected = []
    unresolved = []
    for name in dict.fromkeys(normalize(p["name"]) for p in found):
        group = [p for p in found if normalize(p["name"]) == name]
        if len(group) == 1:
            selected.extend(group)
            continue
        qualified = [p for p in group if any(
            f" {normalize(d['province_name'])} " in query for d in p.get("documents", [])
        )]
        if len(qualified) == 1:
            selected.extend(qualified)
        else:
            unresolved.extend(group)
    return selected, unresolved


def create_app(pipeline_factory=RAGPipeline):
    settings = Settings.from_env()
    app = FastAPI(title="Mây · RAG API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(","),
        allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
    )
    lock = Lock()
    pipeline = None
    # Global demo quota: do not trust client-supplied IP headers through a tunnel.
    quota_lock = Lock()
    requests = deque()
    active = 0
    max_active = max(1, int(os.getenv('CHAT_MAX_CONCURRENT', '1')))
    max_requests = max(1, int(os.getenv('CHAT_REQUESTS_PER_MINUTE', '10')))

    @app.middleware('http')
    async def protect_chat(request, call_next):
        nonlocal active
        if request.method != 'POST' or request.url.path != '/chat':
            return await call_next(request)
        now = time.monotonic()
        with quota_lock:
            while requests and requests[0] <= now - 60:
                requests.popleft()
            if active >= max_active or len(requests) >= max_requests:
                return JSONResponse(status_code=429, content={'detail': 'Trợ lý đang bận. Bạn chờ một chút rồi thử lại nhé.'}, headers={'Retry-After': '10'})
            active += 1
            requests.append(now)
        try:
            return await call_next(request)
        finally:
            with quota_lock:
                active -= 1

    def public_places(records):
        if os.getenv('PUBLIC_DEPLOY', '').lower() != 'true':
            return records
        result = []
        for record in records:
            image = record.get('image', {})
            if image.get('rights_status') == 'permission_required' or not re.match(r'^(CC BY|CC0|Public domain)', image.get('license', ''), re.I):
                record = {k: v for k, v in record.items() if k != 'image'}
            result.append(record)
        return result

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "rag", "pipeline_loaded": pipeline is not None}

    @app.get("/places")
    def list_places():
        return public_places(CATALOGUE)

    @app.get("/sources/{name:path}")
    def source_document(name: str):
        root = settings.raw_dir.resolve()
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".pdf"}:
            raise HTTPException(404, "Tài liệu không tồn tại.")
        return FileResponse(path, media_type="application/pdf" if path.suffix.lower() == ".pdf" else "text/plain; charset=utf-8")

    @app.post("/chat")
    def chat(body: ChatRequest):
        nonlocal pipeline
        question = body.question.strip()
        if not question:
            raise HTTPException(422, "Vui lòng nhập câu hỏi.")
        base = {"answer": "", "sources": [], "places": [], "map_action": "keep", "itinerary": [], "route": None}
        context_text = question + ' ' + ' '.join(m.text for m in body.history[-6:] if m.role == 'user')
        if " an binh " in f" {normalize(question)} " and "cu lao an binh" not in normalize(context_text) and "vinh long" not in normalize(context_text):
            return {**base, "answer": "Bạn đang hỏi An Bình ở tỉnh hoặc thành phố nào? Mình cần làm rõ trước khi đổi bản đồ."}
        found, ambiguous = ambiguous_matches(match_places(question), context_text)
        if ambiguous:
            options = ", ".join(dict.fromkeys(d['province_name'] for p in ambiguous for d in p.get('documents', [])))
            return {**base, "answer": f"Bạn đang hỏi {ambiguous[0]['name']} ở {options}? Hãy cho biết tỉnh hoặc thành phố để mình chọn đúng địa điểm."}
        contextual_question = question
        if not found and re.search(r"\b(o do|noi do|cho do|dia diem nay)\b", normalize(question)):
            for message in reversed(body.history):
                if message.role != "user":
                    continue
                found = match_places(message.text)
                if found:
                    break
        try:
            with lock:
                if pipeline is None:
                    pipeline = pipeline_factory()
                result = pipeline.answer(contextual_question, history=[m.model_dump() for m in body.history])
        except FileNotFoundError:
            raise HTTPException(503, "Chưa có index RAG. Hãy chạy scripts/ingest.py.")
        except ConnectionError:
            raise HTTPException(503, "Không kết nối được Ollama hoặc model chưa sẵn sàng. Hãy kiểm tra Ollama rồi thử lại.")
        except Exception:
            logger.exception("RAG request failed")
            raise HTTPException(503, "RAG chưa sẵn sàng. Hãy kiểm tra index, model embedding và nhật ký backend.")
        if not result.sources:
            return {**base, "answer": result.answer}
        sources = []
        for item in result.sources:
            references = json.loads(item.metadata.get('source_references', '[]'))
            urls = [r['url'] for r in references]
            if not urls:
                urls = re.findall(r'https?://[^\s<>\)\]`]+', item.text)
            if item.source.startswith(("http://", "https://")):
                urls.insert(0, item.source)
            else:
                path = Path(item.source).resolve()
                root = settings.raw_dir.resolve()
                if path.is_relative_to(root) and path.is_file():
                    urls.insert(0, "/sources/" + quote(path.relative_to(root).as_posix()))
            for url in urls:
                if not any(s["url"] == url for s in sources):
                    title = next((r['title'] for r in references if r['url'] == url),
                                 item.metadata.get('section', 'Nguồn tham khảo về điểm đến'))
                    sources.append({"title": title, "url": url})
        # Use evidence-selected IDs, never generated answer text, to resolve maps.
        ids = getattr(result, 'place_ids', [])
        if ids:
            found = [p for identifier in ids for p in CATALOGUE
                     if identifier in p.get('rag_ids', [])]
            found = list({p['id']: p for p in found}.values())
        else:
            # Exclude province aliases masquerading as standalone map destinations.
            from .travel import resolve_provinces
            province_ids = resolve_provinces(question, [d for p in CATALOGUE for d in p.get('documents', [])])
            if province_ids and not any(normalize(p['name']) in normalize(question) for p in found):
                found = []
        itinerary_requested = bool(getattr(result, 'itinerary_ids', [])) or any(term in normalize(question) for term in ("lich trinh", "hanh trinh"))
        itinerary = [p["id"] for p in found] if itinerary_requested else []
        mapped = [p for p in found if p["coordinates"] is not None]
        route = {"kind": "illustrative", "coordinates": [p["coordinates"] for p in mapped]} if len(itinerary) > 1 and len(mapped) == len(found) and all(p.get('map_usage') != 'zoom_only' for p in found) else None
        if route:
            from .advice import distance
            route['distance_m'] = sum(distance(a, b) * 1000 for a, b in
                                      zip(route['coordinates'], route['coordinates'][1:]))
        answer = result.answer
        map_status = ''
        if not found:
            map_status = 'Chưa có vị trí phù hợp để hiển thị; giữ khung nhìn hiện tại.'
        elif len(mapped) != len(found):
            map_status = 'Một số điểm chưa có vị trí xác minh: ' + ', '.join(p['name'] for p in found if p['coordinates'] is None) + '.'
        if route:
            map_status = 'Tuyến minh họa, không phải đường đi thực tế.'
        return {**base, "answer": answer, "sources": sources, "places": public_places(found),
                "map_status": map_status,
                "map_action": "focus" if len(mapped) == 1 else "fit" if mapped else "keep",
                "itinerary": itinerary, "route": route}

    return app


app = create_app()