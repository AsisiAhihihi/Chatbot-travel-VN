"""Offline ingestion and online retrieve-then-generate RAG pipeline."""

from .config import Settings
from .embeddings import SentenceTransformerEmbedder
from .llm import OllamaClient
from .loader import load_documents
from .models import RAGAnswer, SearchResult
from .vector_store import LangChainVectorStore
from .travel import split_travel_document
from .grounding import resolve_request, allowed_document, content_kind
from .advice import attraction_evidence, introduction, itinerary, select_itinerary, price_answer
from langchain_core.documents import Document
import json
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

SYSTEM_PROMPT = (
    "Diễn đạt tự nhiên, ngắn gọn như tư vấn cho khách du lịch. Không nói về chunk, raw data, "
    "metadata, cấu trúc kho dữ liệu hoặc số trải nghiệm cần điền. Nếu thiếu thông tin liên quan, "
    "chỉ nói ngắn gọn điều chưa xác minh; không lặp thông báo kỹ thuật ở từng điểm. "
    "Bạn là Mây, trợ lý du lịch; Mây không phải tên người dùng. Không chào bằng tên chưa được cung cấp. "
    "Mỗi điểm được yêu cầu có một mục riêng. Không chuyển sự kiện hoặc doanh nghiệp giữa các tỉnh. "
    "Chỉ giới thiệu các điểm trong PHẠM VI. Không tự thêm khách sạn, nơi khác hoặc câu hỏi đặt phòng. "
    "Với giới thiệu hai điểm, hướng tới 150–220 từ nếu nguồn đủ; không kéo dài khi thiếu dữ liệu. "
    "Bạn là trợ lý hữu ích. Trả lời bằng tiếng Việt, chỉ dựa trên NGỮ CẢNH được cung cấp. "
    "Nếu ngữ cảnh không đủ để trả lời, hãy nói rõ rằng tài liệu chưa cung cấp thông tin đó. "
    "Không bịa đặt nguồn hoặc sự kiện. Trích URL và ngày nguồn liên quan. "
    "historical_reference là giá lịch sử, không phải báo giá hiện tại; published_reference "
    "là giá được thấy khi tra cứu, chưa xác nhận cho ngày đặt; unknown là chưa có giá xác minh. "
    "Không gán giá nhóm cho cơ sở riêng, không tính tổng khi thiếu đơn vị hoặc thời lượng. "
    "Hỏi ngày đi, số người và nhu cầu trước khi cộng ngân sách. Không bịa quán, homestay, "
    "tọa độ, ảnh hoặc giờ mở cửa. Không dùng tâm tỉnh làm tọa độ điểm đến. "
    "Tên tỉnh cũ là từ khóa địa lý, không phải địa chỉ hành chính đã xác minh."
)


class RAGPipeline:
    def __init__(self, settings: Settings | None = None, embedder=None, llm=None) -> None:
        self.settings = settings or Settings.from_env()
        self.embedder = embedder or SentenceTransformerEmbedder(self.settings.embedding_model)
        self.llm = llm or OllamaClient(self.settings.ollama_base_url, self.settings.ollama_model)

    def ingest(self) -> int:
        if self.settings.chunk_size <= 0 or not 0 <= self.settings.chunk_overlap < self.settings.chunk_size:
            raise ValueError("chunk_overlap must be between 0 and chunk_size")
        documents = load_documents(self.settings.raw_dir)
        if not documents:
            raise FileNotFoundError(f"No non-empty .txt, .md, or .pdf documents found in {self.settings.raw_dir}")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            add_start_index=True,
        )
        chunks = []
        for document in documents:
            if document.metadata.get("province_id"):
                chunks.extend(split_travel_document(
                    document, self.settings.chunk_size, self.settings.chunk_overlap
                ))
            else:
                chunks.extend(splitter.split_documents([document]))
        self.store = LangChainVectorStore.from_documents(
            chunks, self.embedder, self.settings.store_dir
        )
        return len(chunks)

    def _store(self):
        if not getattr(self, "store", None):
            self.store = LangChainVectorStore.load(self.embedder, self.settings.store_dir)
        return self.store

    def request_scope(self, question, history=None):
        payload = self._store().store.get(include=["metadatas", "documents"])
        documents = [Document(page_content=text, metadata=metadata)
                     for text, metadata in zip(payload["documents"], payload["metadatas"])]
        return resolve_request(question, history, documents), documents

    def retrieve(self, question: str, history=None):
        scope, documents = self.request_scope(question, history)
        return self._retrieve_scope(scope, documents)

    def _retrieve_scope(self, scope, documents):
        if scope.clarification:
            return []
        matches = []
        for target in scope.targets:
            candidates = [d for d in documents if allowed_document(d, target, scope.intent)]
            eligible = self._store().similarity_search_with_score(
                scope.question + " " + target.name + " " + ' '.join(scope.preferences),
                k=len(candidates), candidates=candidates)
            for doc, score in eligible[:self.settings.top_k]:
                metadata = {**doc.metadata, "resolved_destination": target.name,
                            "content_kind": content_kind(doc.metadata, doc.page_content)}
                metadata.setdefault("price_status", json.dumps(list(dict.fromkeys(re.findall(
                    r"`(historical_reference|published_reference|unknown)`", doc.page_content)))))
                # Keep business requests row-scoped rather than exposing other businesses.
                text = doc.page_content
                if target.business:
                    from .grounding import contains
                    text = "\n".join(line for line in text.splitlines() if contains(line, target.business))
                    refs = set(re.findall(r'S\d+', text))
                    metadata['source_details'] = "\n".join(
                        line for line in metadata.get('source_details', '').splitlines()
                        if any(f'**{ref}**' in line for ref in refs))
                    metadata['source_urls'] = json.dumps(re.findall(
                        r'https?://\S+', metadata['source_details']), ensure_ascii=False)
                if scope.intent == 'price' and target.place_id:
                    from .grounding import contains
                    table = text.splitlines()
                    headings = [line for line in table if line.startswith('|') and '`' not in line]
                    rows = [line for line in table if line.startswith('|') and '`' in line
                            and contains(line.split('|')[1], target.name)]
                    if not rows:
                        continue
                    text = '\n'.join(headings[:2] + rows)
                    refs = set(re.findall(r'S\d+', text))
                    metadata['source_details'] = '\n'.join(line for line in metadata.get('source_details', '').splitlines()
                                                          if any(f'**{ref}**' in line for ref in refs))
                    metadata['source_urls'] = json.dumps(re.findall(r'https?://[^\s)<>]+', metadata['source_details']))
                    references = json.loads(metadata.get('source_references', '[]'))
                    metadata['source_references'] = json.dumps([r for r in references if r['url'] in json.loads(metadata['source_urls'])], ensure_ascii=False)
                    metadata['price_status'] = json.dumps(list(dict.fromkeys(re.findall(
                        r'`(historical_reference|published_reference|unknown)`', text))))
                matches.append((Document(page_content=text, metadata=metadata), score))
        if not scope.targets:
            # Unknown scope must not fall back to unrelated nationwide recommendations.
            return []
        unique = {}
        for document, score in matches:
            key = (document.metadata.get('source'), document.metadata.get('start_index'), document.page_content)
            unique.setdefault(key, (document, score))
        return [
            SearchResult(
                text=document.page_content + (
                    "\n\nNguồn và thời điểm:\n" + document.metadata["source_details"]
                    if document.metadata.get("source_details") else ""
                ),
                source=str(document.metadata.get("source", "unknown")), score=float(score),
                index=int(document.metadata.get("start_index", index)), metadata=document.metadata,
            ) for index, (document, score) in enumerate(unique.values())
        ]

    def answer(self, question: str, history=None) -> RAGAnswer:
        scope, documents = self.request_scope(question, history)
        if scope.clarification:
            return RAGAnswer(scope.clarification, [])
        results = self._retrieve_scope(scope, documents)
        if not results:
            if scope.region:
                return RAGAnswer('Mình chưa có đủ mô tả điểm đến trong miền này để ghép tuyến có căn cứ. '
                                 'Bạn thích biển, sông nước hay di tích để mình thu hẹp lựa chọn?', [])
            if scope.targets:
                return RAGAnswer('Mình chưa có đủ dữ liệu về nội dung bạn hỏi tại ' + ', '.join(t.name for t in scope.targets)
                                 + '. Mình không dùng thông tin của nơi khác để thay thế.', [])
            return RAGAnswer('Bạn muốn khám phá miền nào, hay đã có điểm đến yêu thích để mình gợi ý?', [])
        place_ids = list(dict.fromkeys(r.metadata['place_id'] for r in results if r.metadata.get('place_id')))
        if scope.intent == 'itinerary':
            from pathlib import Path
            catalogue = json.loads(Path(__file__).with_name('catalogue.json').read_text(encoding='utf-8'))
            selected = select_itinerary(scope, results, catalogue)
            ids = [r.metadata['place_id'] for r in selected]
            return RAGAnswer(itinerary(scope, selected), selected, ids, ids)
        if scope.intent in {'introduction', 'activities', 'discovery'}:
            if scope.intent == 'discovery':
                # Preserve coverage across named provinces/regions before filling top-k.
                chosen = []
                for target in scope.targets:
                    candidate = next((r for r in results if r.metadata.get('province_id') == target.province_id), None)
                    if candidate and candidate not in chosen:
                        chosen.append(candidate)
                results = (chosen + [r for r in results if r not in chosen])[:max(self.settings.top_k, len(chosen))]
                place_ids = [r.metadata['place_id'] for r in results]
            answer = introduction(results, compact=scope.intent == 'discovery')
            if scope.intent == 'discovery':
                answer = 'Một số điểm bạn có thể khám phá:\n\n' + answer
            # Compose directly from typed evidence: no raw fields or group leakage.
            return RAGAnswer(answer, results, place_ids)
        if scope.intent == 'price':
            return RAGAnswer(price_answer(results), results,
                             [t.place_id for t in scope.targets if t.place_id])
        groups = [(t, [r for r in results if r.metadata.get("resolved_destination") == t.name]) for t in scope.targets]
        if any(t.business for t in scope.targets):
            return RAGAnswer("\n\n".join(
                f"### {t.name}\nĐịa phương theo nguồn: "
                + (rows[0].metadata.get('province_name', t.province_id) if rows else t.province_id)
                + ".\n" + "\n".join(dict.fromkeys(r.text for r in rows))
                for t, rows in groups), results)
        if scope.intent == 'accommodation' and all(
                sum(len(r.text.split('Nguồn và thời điểm:')[0].split()) for r in rows) < 160
                for _, rows in groups):
            return RAGAnswer("\n\n".join(
                f"### Lưu trú tại {t.name}\n" + "\n".join(dict.fromkeys(
                    line for r in rows for line in r.text.split('Nguồn và thời điểm:')[0].splitlines()
                    if line.startswith('- ')))
                + "\nNguồn chỉ liệt kê các cơ sở trên, chưa đủ thông tin để đánh giá tiện nghi, vị trí cụ thể hoặc chất lượng. "
                "Chưa có báo giá riêng được xác minh cho ngày đặt."
                for t, rows in groups), results)
        context = "\n\n".join(
            json.dumps(attraction_evidence(item), ensure_ascii=False)
            if item.metadata.get('content_kind') == 'attraction' else
            f"{item.metadata.get('province_name', '')}:\n" + '\n'.join(
                line for line in item.text.splitlines()
                if not re.search(r'place_id|content_type|Tên dùng tìm kiếm|latitude|longitude|image_url|^#', line))
            for item in results)
        prompt = (
            f"NGỮ CẢNH:\n{context}\n\n"
            f"PHẠM VI: {', '.join(t.name for t in scope.targets)}\nÝ ĐỊNH: {scope.intent}\n"
            f"CÂU HỎI: {scope.question}\n\nHãy trả lời dựa trên ngữ cảnh ở trên. "
            "Không coi nguồn lưu trú là mô tả điểm tham quan. Giá phải kèm trạng thái, ngày và điều kiện nguồn."
        )
        answer = self.llm.generate(prompt, SYSTEM_PROMPT)
        forbidden = ('place_id', 'content_type', 'Tên dùng tìm kiếm', 'metadata', 'latitude', 'longitude', 'image_url')
        if any(term.lower() in answer.lower() for term in forbidden):
            answer = self.llm.generate(prompt + '\nViết lại thành lời tư vấn, tuyệt đối không xuất trường nội bộ.', SYSTEM_PROMPT)
        if any(term.lower() in answer.lower() for term in forbidden):
            answer = introduction(results) if place_ids else 'Mình chưa đủ thông tin để diễn giải nội dung này một cách đáng tin cậy.'
        return RAGAnswer(answer, results, place_ids)