"""
Test RAG Phap Ly — Verify ChromaDB retrieval + Legal Agent integration.
Test F&B (tra sua) → expect ND 15/2018, ND 106/2025
Test Tech (AI app) → expect Luat AI 134/2025, Luat An ninh mang
KHONG goi OpenAI chat API (chi embedding) — tiet kiem.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

PASS = 0
FAIL = 0


def test(name, passed, detail=""):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -- {detail}")


def main():
    global PASS, FAIL

    # ===================================================================
    print("\n=== 1. ChromaDB Connection ===")
    # ===================================================================
    from ai_engine.rag.chroma_client import get_chroma_client, get_legal_collection, LEGAL_COLLECTION

    client = get_chroma_client()
    test("ChromaDB connected", client.heartbeat() > 0)

    collection = get_legal_collection()
    count = collection.count()
    test(f"Collection '{LEGAL_COLLECTION}' has documents", count > 0, f"count={count}")
    test("Has 12 documents", count == 12, f"count={count}")

    # ===================================================================
    print("\n=== 2. Retriever — F&B Query ===")
    # ===================================================================
    from ai_engine.rag.retriever import retrieve_legal_context, format_legal_context

    # Test F&B
    docs_fb = retrieve_legal_context(
        idea="Mo quan tra sua healthy cho gymer tai TP.HCM",
        industry="F&B",
        top_k=5,
    )
    test("F&B: got results", len(docs_fb) > 0, f"got {len(docs_fb)}")
    test("F&B: got 5 results", len(docs_fb) == 5)

    # Check NĐ 15/2018 (ATTP) appears
    fb_sources = [d["source"] for d in docs_fb]
    test("F&B: contains ND 15/2018 (ATTP)",
         any("15/2018" in s for s in fb_sources),
         f"sources: {fb_sources}")

    # Check NĐ 115/2018 (xu phat ATTP) or NĐ 106/2025 (PCCC)
    test("F&B: contains ND 115/2018 or ND 106/2025",
         any("115/2018" in s or "106/2025" in s for s in fb_sources),
         f"sources: {fb_sources}")

    # Print F&B results for visual inspection
    print("\n  [INFO] F&B top 5 results:")
    for i, doc in enumerate(docs_fb):
        print(f"    [{i+1}] {doc['source']} (score={doc['relevance_score']}) — {doc['content'][:60]}...")

    # ===================================================================
    print("\n=== 3. Retriever — Tech/AI Query ===")
    # ===================================================================

    docs_tech = retrieve_legal_context(
        idea="Xay dung app AI chatbot tu van suc khoe",
        industry="Tech, AI, healthtech",
        top_k=5,
    )
    test("Tech: got results", len(docs_tech) > 0)

    tech_sources = [d["source"] for d in docs_tech]
    test("Tech: contains Luat AI 134/2025",
         any("134/2025" in s or "AI" in s for s in tech_sources),
         f"sources: {tech_sources}")

    test("Tech: contains Luat An ninh mang or ND 13/2023",
         any("An ninh" in s or "13/2023" in s for s in tech_sources),
         f"sources: {tech_sources}")

    print("\n  [INFO] Tech top 5 results:")
    for i, doc in enumerate(docs_tech):
        print(f"    [{i+1}] {doc['source']} (score={doc['relevance_score']}) — {doc['content'][:60]}...")

    # ===================================================================
    print("\n=== 4. format_legal_context() ===")
    # ===================================================================

    formatted = format_legal_context(docs_fb)
    test("Formatted is non-empty", len(formatted) > 100)
    test("Formatted has 'Van ban phap ly'", "Van ban phap ly" in formatted or "pháp lý" in formatted.lower())
    test("Formatted has NĐ/Luật name", any(s in formatted for s in fb_sources))
    test("Formatted has cite instruction", "cite" in formatted.lower() or "Cite" in formatted)

    # Empty case
    empty = format_legal_context([])
    test("Empty docs returns empty string", empty == "")

    # ===================================================================
    print("\n=== 5. Legal Agent RAG Integration (mock LLM) ===")
    # ===================================================================

    from unittest.mock import patch, MagicMock
    from ai_engine.agents.legal import LegalAgent

    agent = LegalAgent()
    test("LegalAgent has analyze() override", hasattr(agent, 'analyze'))
    test("LegalAgent MODEL = gpt-4o", agent.MODEL == "gpt-4o")

    # Mock the LLM call but let RAG (embedding) run real
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock legal analysis with RAG"
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 300
    mock_response.usage.total_tokens = 800

    with patch.object(agent.client.chat.completions, 'create', return_value=mock_response) as mock_create:
        result = agent.analyze(
            "Mo quan tra sua healthy tai TP.HCM",
            industry="F&B",
        )

        test("analyze() returns dict", isinstance(result, dict))
        test("Result has rag_sources", "rag_sources" in result)
        test("rag_sources > 0 (RAG working)", result.get("rag_sources", 0) > 0,
             f"rag_sources={result.get('rag_sources')}")

        # Check that the LLM prompt includes RAG context
        call_args = mock_create.call_args
        messages = call_args.kwargs.get("messages") or call_args[1].get("messages")
        user_msg = messages[1]["content"]
        test("Prompt includes RAG context", "pháp lý" in user_msg.lower() or "phap ly" in user_msg.lower() or "15/2018" in user_msg)
        test("Prompt includes idea", "tra sua" in user_msg.lower() or "TP.HCM" in user_msg)

    # ===================================================================
    print("\n=== 6. Legal Agent — Fallback when ChromaDB fails ===")
    # ===================================================================

    with patch('ai_engine.agents.legal.retrieve_legal_context', side_effect=Exception("DB down")):
        with patch.object(agent.client.chat.completions, 'create', return_value=mock_response):
            result = agent.analyze("Test idea", "Tech")
            test("Fallback: analyze() still works", result is not None)
            test("Fallback: rag_sources = 0", result.get("rag_sources", -1) == 0)
            test("Fallback: content exists", "content" in result)

    # ===================================================================
    # SUMMARY
    # ===================================================================
    print("\n" + "=" * 55)
    print(f"  RAG TEST RESULTS: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")
    print("=" * 55)
    return FAIL == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
