"""Ask a question against the local vector index."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.pipeline import RAGPipeline, SYSTEM_PROMPT


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask your local RAG chatbot")
    parser.add_argument("question", nargs="+", help="Question to ask")
    args = parser.parse_args()
    question = " ".join(args.question)
    pipeline = RAGPipeline()
    try:
        results = pipeline.retrieve(question)
        if not results:
            print("Chưa tìm thấy đoạn tài liệu phù hợp.")
            return 0
        try:
            context = "\n\n".join(f"[Nguồn: {r.source}]\n{r.text}" for r in results)
            prompt = f"NGỮ CẢNH:\n{context}\n\nCÂU HỎI: {question}\n\nHãy trả lời dựa trên ngữ cảnh ở trên."
            response = pipeline.llm.generate(prompt, SYSTEM_PROMPT)
            print(f"\n{response}")
        except ConnectionError as exc:
            print(f"\nLLM chưa khả dụng: {exc}\nCác đoạn truy xuất được (chưa phải câu trả lời do LLM tạo):")
            for result in results:
                print(f"\n[{result.source} · relevance {result.score:.3f}]\n{result.text}")
        print("\nNguồn:")
        for result in results:
            print(f"- {result.source} (relevance {result.score:.3f})")
    except Exception as exc:
        print(f"Query failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())