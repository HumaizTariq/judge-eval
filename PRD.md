# Judge Eval (PRD, draft v0.1)

Status: APPROVED 2026-10-20 (flaws as drafted, run on the 2 Gong profiles). Built and run 2026-10-20: 35 calls, $0.13, see README.md. Flaw 2 became "generic proof points": the profile has no source URLs to remove. Portfolio piece next to `gtm-mcp/`. OpenAI only: no treg, Tavily, Exa, AI Ark or Ocean.

The GTM agent (an open-source, MIT-licensed CrewAI agent system; credit in the README) has an AI judge: gpt-4o scores every deliverable 0-10 and sends it back for revision below 7, at most twice. Every run trusts that score. Nobody has checked whether the score is stable, or whether it drops when the work is bad. This piece checks both.

## Questions it answers
1. **Consistency:** the same deliverable judged N times. How far do the scores spread? How often does approve/reject flip?
2. **Sensitivity:** the same deliverable with one flaw planted on purpose. Does the score drop, and does the judge name the flaw in `issues`?

## Rules
- The GTM agent is not changed. The eval imports its judge agent (`gtm_engineer_agent()`) and the `ReviewVerdict` schema read-only, through the agent's own environment (`uv run --directory <agent> python <eval script>`), and sends the same review prompt `_judge` sends (copied into the eval, with the research criteria). So it measures the real judge, not a look-alike. If the prompt in the agent changes, the eval's copy is updated by hand; a test checks the copy still matches the agent's source.
- Inputs are saved deliverables only, never a new research run. Company-level public data; no contacts.
- Hard cap: `--max-calls` (default 40), checked before the first call. Cost printed from token usage after each call.

## Inputs
| Deliverable | From |
|---|---|
| Gong client profile (good) | `output/gong-io/profile.json` |
| Gong client profile (made without web search, weaker) | `output/gong-io-run1-no-search/profile.json` |
| Prospect briefs | `output/*/prospect_brief.json`, once `run_prospect_research` has made some |

Planted flaws, one per variant, made by code from the good profile (no LLM):
1. **Vague ICP:** industries become "B2B companies", size range removed.
2. **No sources:** every source URL removed.
3. **Marketing copy:** `what_they_do` replaced with the company's own tagline-style fluff.
4. **Wrong buyer:** buyer personas swapped for titles that don't buy the product (e.g. "Head of Facilities").
5. **Contradiction:** a disqualifier that matches the ICP's own industry.

## Method
- Each deliverable judged 5 times (default `--repeats 5`), same prompt, the agent's own model settings.
- 2 base + 5 variants = 7 deliverables x 5 = 35 calls (under the cap).
- Per deliverable: mean, min, max, standard deviation of score; approve rate; for variants, how many runs named the planted flaw (keyword match on `issues`, listed per variant).

## Output
- `results/<date>/verdicts.jsonl`: one line per call (deliverable, repeat, score, approved, issues, tokens, cost).
- `results/<date>/report.md`: the table, plus a short "what this means" (e.g. "the no-sources variant still passed 4/5 times: the judge does not check sources").
- Optional page later: the same table as an artifact for the portfolio.

## Cost
About 1,000-2,500 tokens per call on gpt-4o, so about $0.005-0.012 per call; 35 calls is about $0.20-0.45. One run, then reruns only when something changes.

## Build
- Python, own folder `judge-eval/`, run through the agent's environment (above).
- `variants.py`: the 5 planted flaws, pure functions. Tests on the fixture profile, no API.
- `run_eval.py`: loads inputs, applies the cap, calls the judge, writes `verdicts.jsonl` and `report.md`. A `--dry-run` prints the call plan and estimated cost without calling.
- Tests: variants change only what they say; cap refuses; report math on fake verdicts; prompt copy matches the agent's `_judge` text.

## Done when
- Tests pass.
- One real run (35 calls) with `report.md`, cost recorded.
- README in the Loom format: question, method, table, the one finding that matters, cost; credit + MIT notice.

## Open questions for the user
1. Approve the 5 planted flaws, or change them?
2. Run now on the 2 Gong profiles only, or wait until a few prospect briefs exist?
