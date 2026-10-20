# Judge Eval

Does an AI judge actually judge? A GTM engineer agent uses gpt-4o as a judge: it scores every research deliverable 0-10 and sends it back for revision below 7. Every run trusts that score. This eval checks two things:

1. **Consistency:** the same deliverable judged 5 times. How much does the score move?
2. **Sensitivity:** the same deliverable with one flaw planted on purpose. Does the score drop, and does the judge say why?

## Method
- Inputs: two saved client profiles (Gong, public data): a good one, and an earlier one made without web search.
- Five planted flaws, made by code from the good profile, one per copy (`variants.py`): vague ICP, generic proof points, hype copy as the company description, wrong buyer titles, a disqualifier that contradicts the ICP.
- 7 deliverables x 5 repeats = 35 calls to the agent's real judge, imported unchanged, with the same prompt (a test checks the copy still matches the agent's source).
- Hard cap on calls before the first one; cost from token counts.

## Results (2026-10-20, 35 calls, $0.13)
| Deliverable | Scores | Mean | Approved | Flaw named |
|---|---|---|---|---|
| Good profile | 8-9 | 8.2 | 5/5 | - |
| Profile made without web search | 6-9 | 7.8 | 4/5 | - |
| + vague ICP | 5-8 | 5.8 | 1/5 | 4/5 |
| + generic proof points | 5-6 | 5.2 | 0/5 | 5/5 |
| + hype copy as description | 6-8 | 7.6 | **4/5** | **1/5** |
| + wrong buyer titles | 5-6 | 5.2 | 0/5 | 5/5 |
| + contradicting disqualifier | 5-6 | 5.4 | 0/5 | 5/5 |

**The finding that matters:** the judge reliably catches structural flaws (wrong buyer, contradiction, generic proof) but approves hype copy 4 times out of 5, at score 8 with no issues listed, and once let a "B2B companies" ICP through at 8. One judge call is a noisy gate. Fixes: a cheap deterministic check before the judge (hype words, required size range), or the lowest of 2-3 judge calls on borderline scores.

Full table and notes: `results/2026-10-20/report.md`. Every verdict with the judge's exact issues: `results/2026-10-20/verdicts.jsonl`.

## Run
```
python -m unittest discover -s tests                                    # no API calls; set GTM_AGENT_DIR=<agent folder> to also check the prompt copy
cd <agent folder>
uv run python <this folder>/run_eval.py --dry-run                       # plan and cost, no calls
PYTHONIOENCODING=utf-8 uv run python <this folder>/run_eval.py          # needs OPENAI_API_KEY in the environment
```
`PYTHONIOENCODING=utf-8` avoids a harmless Windows console warning from the agent framework's emoji output.

## Credits
The GTM engineer agent whose judge is tested here is DFY Automation's open-source GTM Engineer (community edition), MIT licensed: https://github.com/dfyautomation/gtm-engineer-community. This eval imports its judge read-only and does not include or modify its code.
