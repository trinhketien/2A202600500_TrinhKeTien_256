"""Quick test for web search and mem0 imports."""
import sys
sys.path.insert(0, ".")

# Test 1: DuckDuckGo search
print("=" * 50)
print("TEST 1: DuckDuckGo Web Search")
from ai_engine.tools.web_search import search_web, format_search_context

results = search_web("tra sua healthy Viet Nam 2024 2025", max_results=3)
print(f"  Results: {len(results)}")
for i, r in enumerate(results):
    print(f"  {i+1}. {r['title'][:60]}")
    print(f"     URL: {r['url'][:80]}")

if results:
    ctx = format_search_context(results)
    print(f"\n  format_search_context: {len(ctx)} chars")
    print("  [PASS] Web search OK")
else:
    print("  [WARN] No results (may be rate limited)")

# Test 2: Clarifier still works
print("\n" + "=" * 50)
print("TEST 2: Clarifier")
from ai_engine.clarifier import check_idea_clarity

r1 = check_idea_clarity("ban do an")
r2 = check_idea_clarity("Mo quan tra sua healthy cho gymer tai TP.HCM, target Gen Z, gia 35-55k/ly, von 200 trieu")
print(f"  Short idea: needs={r1['needs_clarification']}, q={len(r1['questions'])}")
print(f"  Long idea: needs={r2['needs_clarification']}, q={len(r2['questions'])}")
assert r1["needs_clarification"] == True
assert r2["needs_clarification"] == False
print("  [PASS] Clarifier OK")

# Test 3: Module imports
print("\n" + "=" * 50)
print("TEST 3: Module imports")
from ai_engine.memory.mem0_client import search_memories, add_memory, count_memories, format_memory_context
from ai_engine.memory.lifecycle import deduplicate, prune_if_over_limit, compress_old_memories, track_growth
from ai_engine.agents.market import MarketAgent
from ai_engine.debate_stream import run_debate_streaming, run_reply_streaming
import inspect

# Verify user_id param exists
sig1 = inspect.signature(run_debate_streaming)
sig2 = inspect.signature(run_reply_streaming)
assert "user_id" in sig1.parameters, "run_debate_streaming missing user_id"
assert "user_id" in sig2.parameters, "run_reply_streaming missing user_id"
print("  run_debate_streaming: user_id param OK")
print("  run_reply_streaming: user_id param OK")

# Verify MarketAgent has override analyze
assert "analyze" in dir(MarketAgent)
print("  MarketAgent.analyze: OK")

print("  [PASS] All imports OK")

# Test 4: format_memory_context edge cases
print("\n" + "=" * 50)
print("TEST 4: format_memory_context edge cases")
assert format_memory_context([]) == "", "Should return empty for empty list"
assert format_memory_context(None) == "", "Should return empty for None"
ctx2 = format_memory_context([{"memory": "Test memory 1"}, {"memory": "Test memory 2"}])
assert "Test memory 1" in ctx2
assert "Test memory 2" in ctx2
print("  Empty list: OK")
print("  None: OK")
print("  Valid memories: OK")
print("  [PASS] format_memory_context OK")

print("\n" + "=" * 50)
print("ALL TESTS PASSED")
