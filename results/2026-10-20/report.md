| Deliverable | Scores (min-max) | Mean | Stdev | Approved | Flaw named |
|---|---|---|---|---|---|
| gong_profile | 8-9 | 8.2 | 0.4 | 5/5 | - |
| gong_profile_no_search | 6-9 | 7.8 | 0.98 | 4/5 | - |
| gong_profile+vague_icp | 5-8 | 5.8 | 1.17 | 1/5 | 4/5 |
| gong_profile+unsupported_proof | 5-6 | 5.2 | 0.4 | 0/5 | 5/5 |
| gong_profile+marketing_copy | 6-8 | 7.6 | 0.8 | 4/5 | 1/5 |
| gong_profile+wrong_buyer | 5-6 | 5.2 | 0.4 | 0/5 | 5/5 |
| gong_profile+contradiction | 5-6 | 5.4 | 0.49 | 0/5 | 5/5 |

35 judge calls, estimated OpenAI cost $0.1328 (token counts x the agent's own gpt-4o prices).

"Flaw named" is a keyword match on the judge's issues (see variants.py); read verdicts.jsonl for the exact wording.

## What this means (written by hand after reading verdicts.jsonl)
- **Stable on good work.** The good profile scored 8-9 every time (stdev 0.4), approved 5/5.
- **Catches structural flaws.** Generic proof points, wrong buyer titles and a self-contradicting disqualifier were rejected 5/5, and the judge named the flaw each time.
- **Misses marketing fluff.** Replacing the company description with hype copy was approved 4/5 times, at score 8 with no issues listed. Only 1 of 5 runs flagged it.
- **A vague ICP sometimes slips.** "B2B companies" with no size range was rejected 4/5, but one run approved it at 8 with no issues.
- **Weak vs good is close.** The profile made without web search (with "inferred" markers) averaged 7.8 vs 8.2 and passed 4/5. The judge barely separates them.
- **Takeaway for the agent:** one judge call is a noisy gate. Cheap fixes would be a deterministic check before the judge (banned hype words, required size range) or taking the lowest of 2-3 judge calls on borderline scores.
