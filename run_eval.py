"""Judge eval: is the GTM agent's AI judge consistent, and does it catch planted flaws?

Run through the agent's own environment so the real judge is used, unchanged:

    uv run --directory <agent> python <this folder>/run_eval.py --dry-run
    uv run --directory <agent> python <this folder>/run_eval.py

The agent folder must be the working directory (its output/ is read from there).
"""

import argparse
import json
import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from variants import VARIANTS, flaw_named  # noqa: E402

HERE = Path(__file__).parent
EST_USD_PER_CALL = 0.012  # upper estimate, gpt-4o, ~2,500 tokens

# Copied from the agent's _judge() and quality_gate() (research criteria).
# tests/test_eval.py checks these strings still appear in the agent's source.
PROMPT_LINES = [
    "Review this deliverable from a specialist crew.\n\n",
    "Job: {job} | mode: {mode} | company: {company}\n\n",
    "Deliverable:\n{deliverable}\n\n",
    "Score it 0-10 and approve (approved=true) if it scores 7 or ",
    "higher. A 7 means good enough to act on today, not perfect. {criteria} ",
    "Reject only for flaws that would materially hurt an outbound ",
    "campaign, and give concrete revision_instructions when you do.",
]
RESEARCH_CRITERIA = ("For research: ICPs must name real industries/sizes/titles and "
                     "personalization angles must cite concrete facts.")

BASES = {
    "gong_profile": "output/gong-io/profile.json",
    "gong_profile_no_search": "output/gong-io-run1-no-search/profile.json",
}
VARIANT_BASE = "gong_profile"


def build_prompt(deliverable_json: str, company: str) -> str:
    return "".join(PROMPT_LINES).format(job="research", mode="client", company=company,
                                        deliverable=deliverable_json, criteria=RESEARCH_CRITERIA)


def load_deliverables(agent_dir: Path) -> dict[str, tuple[str, dict]]:
    """name -> (variant name or "", profile dict)."""
    bases = {name: json.loads((agent_dir / rel).read_text(encoding="utf-8"))
             for name, rel in BASES.items()}
    out = {name: ("", p) for name, p in bases.items()}
    for vname, fn in VARIANTS.items():
        out[f"{VARIANT_BASE}+{vname}"] = (vname, fn(bases[VARIANT_BASE]))
    return out


def summarize(verdicts: list[dict]) -> list[dict]:
    rows = []
    for name in dict.fromkeys(v["deliverable"] for v in verdicts):
        vs = [v for v in verdicts if v["deliverable"] == name]
        scores = [v["score"] for v in vs]
        row = {"deliverable": name, "variant": vs[0]["variant"], "n": len(vs),
               "mean": round(statistics.fmean(scores), 2), "min": min(scores), "max": max(scores),
               "stdev": round(statistics.pstdev(scores), 2),
               "approved": sum(v["approved"] for v in vs)}
        if row["variant"]:
            row["flaw_named"] = sum(flaw_named(row["variant"], v["issues"]) for v in vs)
        rows.append(row)
    return rows


def report_md(rows: list[dict], total_usd: float, calls: int) -> str:
    lines = ["| Deliverable | Scores (min-max) | Mean | Stdev | Approved | Flaw named |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        named = f"{r['flaw_named']}/{r['n']}" if r["variant"] else "-"
        lines.append(f"| {r['deliverable']} | {r['min']}-{r['max']} | {r['mean']} | "
                     f"{r['stdev']} | {r['approved']}/{r['n']} | {named} |")
    lines.append("")
    lines.append(f"{calls} judge calls, estimated OpenAI cost ${total_usd:.4f} "
                 "(token counts x the agent's own gpt-4o prices).")
    lines.append("")
    lines.append("\"Flaw named\" is a keyword match on the judge's issues (see variants.py); "
                 "read verdicts.jsonl for the exact wording.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--max-calls", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    agent_dir = Path.cwd()
    deliverables = load_deliverables(agent_dir)
    planned = len(deliverables) * args.repeats
    print(f"Plan: {len(deliverables)} deliverables x {args.repeats} repeats = {planned} calls, "
          f"at most ~${planned * EST_USD_PER_CALL:.2f}")
    if planned > args.max_calls:
        sys.exit(f"Refused: {planned} calls is over --max-calls {args.max_calls}")
    if args.dry_run:
        for name in deliverables:
            print(" ", name)
        return

    # Imported only for a real run: the agent's own judge, schema and prices.
    from gtm_engineer.main import gtm_engineer_agent
    from gtm_engineer.schemas import CompanyProfile, ReviewVerdict
    from gtm_engineer.telemetry import estimate_llm_cost

    out_dir = HERE / "results" / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    verdict_path = out_dir / "verdicts.jsonl"
    verdicts, total = [], 0.0
    with verdict_path.open("w", encoding="utf-8") as f:
        for name, (variant, profile) in deliverables.items():
            deliverable_json = CompanyProfile.model_validate(profile).model_dump_json(indent=2)
            prompt = build_prompt(deliverable_json, profile.get("domain", ""))
            for i in range(args.repeats):
                out = gtm_engineer_agent().kickoff(prompt, response_format=ReviewVerdict)
                usage = out.usage_metrics or {}
                if hasattr(usage, "model_dump"):
                    usage = usage.model_dump()
                cost = estimate_llm_cost({"judge": {"model": "openai/gpt-4o", **usage}})
                total += cost
                v = out.pydantic
                row = {"deliverable": name, "variant": variant, "repeat": i + 1,
                       "score": v.score, "approved": v.approved, "issues": v.issues,
                       "prompt_tokens": usage.get("prompt_tokens", 0),
                       "completion_tokens": usage.get("completion_tokens", 0),
                       "est_cost_usd": cost}
                verdicts.append(row)
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"{name} #{i + 1}: score {v.score}, approved={v.approved}, ${cost:.4f}")

    (out_dir / "report.md").write_text(report_md(summarize(verdicts), total, len(verdicts)),
                                       encoding="utf-8")
    print(f"Wrote {verdict_path} and report.md, total ~${total:.4f}")


if __name__ == "__main__":
    main()
