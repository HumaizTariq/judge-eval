"""Planted flaws: each takes a good client profile (a dict) and returns a copy
with exactly one flaw. Pure functions, no LLM.

FLAW_KEYWORDS lists words that show the judge named the flaw in its `issues`.
It is a coarse check; the report keeps every issue so it can be read by hand.
"""

import copy


def vague_icp(p: dict) -> dict:
    p = copy.deepcopy(p)
    p["icp"]["industries"] = ["B2B companies"]
    p["icp"]["company_size_range"] = ""
    return p


def unsupported_proof(p: dict) -> dict:
    # The agent's profile has no source URLs, so "no sources" means proof
    # points with no named customer and no number.
    p = copy.deepcopy(p)
    p["proof_points"] = ["Many leading companies use the platform.",
                         "Customers see great results.",
                         "Trusted by top revenue teams."]
    return p


def marketing_copy(p: dict) -> dict:
    p = copy.deepcopy(p)
    p["what_they_do"] = ("The world's #1 revolutionary AI platform that transforms "
                         "everything about how you win. Unleash the power of reality.")
    return p


def wrong_buyer(p: dict) -> dict:
    p = copy.deepcopy(p)
    p["icp"]["buyer_personas"] = ["Head of Facilities", "Office Manager", "IT Helpdesk Lead"]
    return p


def contradiction(p: dict) -> dict:
    p = copy.deepcopy(p)
    industry = p["icp"]["industries"][0]
    p["icp"]["disqualifiers"] = p["icp"]["disqualifiers"] + [f"{industry} companies"]
    return p


VARIANTS = {
    "vague_icp": vague_icp,
    "unsupported_proof": unsupported_proof,
    "marketing_copy": marketing_copy,
    "wrong_buyer": wrong_buyer,
    "contradiction": contradiction,
}

FLAW_KEYWORDS = {
    "vague_icp": ["vague", "generic", "b2b companies", "size", "broad", "industr"],
    "unsupported_proof": ["proof", "evidence", "named", "specific", "unsupported", "generic", "vague"],
    "marketing_copy": ["marketing", "fluff", "hype", "buzzword", "superlative", "promotional", "vague"],
    "wrong_buyer": ["persona", "buyer", "facilities", "office manager", "helpdesk", "title"],
    "contradiction": ["contradict", "conflict", "inconsistent", "disqualif"],
}


def flaw_named(variant: str, issues: list[str]) -> bool:
    text = " ".join(issues).lower()
    return any(k in text for k in FLAW_KEYWORDS.get(variant, []))
