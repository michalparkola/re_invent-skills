#!/usr/bin/env python3
"""Build a self-contained, tabbed HTML report of a discovery interview.

Usage:
  build_report.py --turns turns.json --report report.json --out "Name.html"

The script validates the data, then copies assets/report.html with the data in it.
The template renders the tabs: overview, transcript with margin notes, notes by theme, findings.
The script writes nothing when a check fails.
See references/data-format.md for the input contract.
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TYPE_KEYS = ["job", "pain", "workaround", "signal", "play-good", "play-distort", "play-missed"]
EVIDENCE = {"job", "pain", "workaround", "signal"}
MOVES = {"play-good", "play-distort", "play-missed"}
PART_TYPES = {"interviewee": EVIDENCE, "interviewer": MOVES}
STATUSES = ["supported", "contradicted", "open"]

LANGS = ["pl", "en"]  # UI labels live in assets/report.html
TEMPLATE = HERE.parent / "assets" / "report.html"
SLOT = '<script type="application/json" id="report-data">null</script>'


def validate(turns, rep):
    errors = []
    by_id = {t["id"]: t for t in turns}
    order = {t["id"]: i for i, t in enumerate(turns)}
    meta = rep.get("meta", {})
    speakers = meta.get("speakers", {})
    if meta.get("lang") not in LANGS:
        errors.append(f"meta.lang must be one of {LANGS}")
    for t in turns:
        if t["sp"] not in speakers:
            errors.append(f"{t['id']}: speaker {t['sp']} not in meta.speakers")
    roles = {s.get("role") for s in speakers.values()}
    if not {"interviewer", "interviewee"} <= roles:
        errors.append("meta.speakers needs at least one interviewer and one interviewee")

    notes = rep.get("notes", [])
    ids = [n.get("id") for n in notes]
    for x in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate note id {x}")
    for n in notes:
        nid = n.get("id")
        if n.get("type") not in TYPE_KEYS:
            errors.append(f"{nid}: bad type {n.get('type')} (use {', '.join(TYPE_KEYS)})")
            continue
        t = by_id.get(n.get("turn"))
        if not t:
            errors.append(f"{nid}: no turn {n.get('turn')}")
            continue
        n["pos"] = t["text"].find(n.get("quote", "\0"))
        if n["pos"] < 0:
            errors.append(f"{nid} {t['id']}: quote not found: {n.get('quote')!r}")
        role = speakers.get(t["sp"], {}).get("role")
        if n["type"] in EVIDENCE and role != "interviewee":
            errors.append(f"{nid}: {n['type']} must quote an interviewee turn (the interviewee's own words), {t['id']} is {role}")
        if n["type"] in ("play-good", "play-distort") and role != "interviewer":
            errors.append(f"{nid}: {n['type']} must quote an interviewer turn, {t['id']} is {role}")

    secs = rep.get("sections", [])
    for s in secs:
        if s.get("start") not in by_id:
            errors.append(f"section start missing {s.get('start')}")
    starts = [order.get(s.get("start"), -1) for s in secs]
    if not secs or starts[0] != 0:
        errors.append("sections must start at the first turn")
    elif starts != sorted(starts):
        errors.append("sections not in transcript order")

    known = set(ids)
    used = []
    for p in rep.get("groups", {}).get("parts", []):
        if p.get("id") not in PART_TYPES:
            errors.append(f"group part id must be one of {list(PART_TYPES)}")
            continue
        for g in p.get("groups", []):
            for nid in g.get("notes", []):
                used.append(nid)
                n = next((x for x in notes if x.get("id") == nid), None)
                if n is None:
                    errors.append(f"group note {nid} does not exist")
                elif n.get("type") in TYPE_KEYS and n["type"] not in PART_TYPES[p["id"]]:
                    errors.append(f"{nid} ({n['type']}) does not belong in part {p['id']}")
    for nid in known - set(used):
        errors.append(f"{nid} not in any group")
    for nid in {x for x in used if used.count(x) > 1}:
        errors.append(f"{nid} in more than one group")

    f = rep.get("findings", {})
    for h in f.get("hypotheses", []):
        if h.get("status") not in STATUSES:
            errors.append(f"hypothesis {h.get('claim')!r}: status must be one of {STATUSES}")
        for nid in h.get("evidence", []):
            if nid not in known:
                errors.append(f"hypothesis {h.get('claim')!r}: unknown note {nid}")
    for q in f.get("next_questions", []):
        for nid in q.get("sources", []):
            if nid not in known:
                errors.append(f"question {q.get('question')!r}: unknown note {nid}")

    if "—" in json.dumps(rep, ensure_ascii=False):
        errors.append("em dash in report copy")
    return errors


def build(turns, rep):
    """Put the data into the template. The template renders the page in the browser."""
    for n in rep.get("notes", []):
        n.pop("pos", None)
    data = json.dumps({"turns": turns, "report": rep}, ensure_ascii=False)
    data = data.replace("<", "\\u003c")
    page = TEMPLATE.read_text()
    assert page.count(SLOT) == 1, "template slot missing"
    return page.replace(SLOT, SLOT.replace(">null<", f">{data}<"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--turns", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    turns = json.loads(a.turns.read_text())
    rep = json.loads(a.report.read_text())
    errors = validate(turns, rep)
    if errors:
        print(f"{len(errors)} problem(s), nothing written:")
        print("\n".join("  " + e for e in errors))
        sys.exit(1)
    page = build(turns, rep)
    a.out.write_text(page)
    c = {k: sum(1 for n in rep["notes"] if n["type"] == k) for k in TYPE_KEYS}
    print(f"OK {a.out} ({len(page) // 1024} KB): {len(rep['notes'])} notes, {len(rep['sections'])} sections")
    print("  " + ", ".join(f"{k} {v}" for k, v in c.items()))


if __name__ == "__main__":
    main()
