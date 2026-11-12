#!/usr/bin/env python3
"""Build a self-contained, tabbed HTML report of a discovery interview.

Usage:
  build_report.py --turns turns.json --report report.json --out "Name.html"

Tabs: overview, transcript with margin notes, notes by theme, findings.
The script validates the data first and writes nothing when a check fails.
See references/data-format.md for the input contract.
"""
import argparse, html, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS_PATH = HERE.parent / "assets" / "style.css"

TYPE_KEYS = ["job", "pain", "workaround", "signal", "play-good", "play-distort", "play-missed"]
EVIDENCE = {"job", "pain", "workaround", "signal"}
MOVES = {"play-good", "play-distort", "play-missed"}
PART_TYPES = {"interviewee": EVIDENCE, "interviewer": MOVES}
STATUSES = ["supported", "contradicted", "open"]

UI = {
    "pl": {
        "types": ["Zadanie", "Problem", "Obecne rozwiązanie", "Sygnał", "Dobry ruch", "Zniekształcenie", "Utracona okazja"],
        "status": {"supported": "Potwierdzona", "contradicted": "Obalona", "open": "Otwarta"},
        "tabs": ["Przegląd", "Transkrypt", "Notatki według tematów", "Wnioski"],
        "min": "min", "turns": "wypowiedzi", "notes": "notatek", "part": "Część",
        "topics": "Tematy rozmowy", "by_type": "Wszystkie notatki według typu", "show": "Pokaż:",
        "all": "Wszystkie", "none": "Żadne", "jump": "Przejdź do cytatu", "in_tr": "w transkrypcie",
        "hyp": "Hipotezy", "next": "Pytania na następną rozmowę", "evidence": "Dowody:", "sources": "Z rozmowy:",
        "footer": "Transkrypt: automatyczna transkrypcja, scalona w wypowiedzi, bez zmian w brzmieniu. "
                  "Cytaty w notatkach to dokładny tekst transkryptu. Nagłówki, notatki i wnioski to interpretacja autora.",
    },
    "en": {
        "types": ["Job", "Pain", "Current workaround", "Signal", "Good move", "Distortion", "Missed opportunity"],
        "status": {"supported": "Supported", "contradicted": "Contradicted", "open": "Open"},
        "tabs": ["Overview", "Transcript", "Notes by theme", "Findings"],
        "min": "min", "turns": "turns", "notes": "notes", "part": "Part",
        "topics": "Topics", "by_type": "All notes by type", "show": "Show:",
        "all": "All", "none": "None", "jump": "Go to quote", "in_tr": "in transcript",
        "hyp": "Hypotheses", "next": "Questions for the next interview", "evidence": "Evidence:", "sources": "From the call:",
        "footer": "Transcript: automatic transcription merged into turns, wording unchanged. "
                  "Note quotes are exact transcript text. Headings, notes and findings are the author's interpretation.",
    },
}
esc = html.escape


def validate(turns, rep):
    errors = []
    by_id = {t["id"]: t for t in turns}
    order = {t["id"]: i for i, t in enumerate(turns)}
    meta = rep.get("meta", {})
    speakers = meta.get("speakers", {})
    if meta.get("lang") not in UI:
        errors.append(f"meta.lang must be one of {list(UI)}")
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
    meta = rep["meta"]
    L = UI[meta["lang"]]
    TYPES = list(zip(TYPE_KEYS, L["types"]))
    LABEL = dict(TYPES)
    speakers = meta["speakers"]
    by_id = {t["id"]: t for t in turns}
    order = {t["id"]: i for i, t in enumerate(turns)}
    notes = rep["notes"]
    nmap = {n["id"]: n for n in notes}
    counts = {k: sum(1 for n in notes if n["type"] == k) for k in TYPE_KEYS}

    notes_by_turn = {}
    for n in notes:
        notes_by_turn.setdefault(n["turn"], []).append(n)
    for lst in notes_by_turn.values():
        lst.sort(key=lambda n: n["pos"])

    def render_text(t):
        text, ns = t["text"], notes_by_turn.get(t["id"], [])
        if not ns:
            return esc(text)
        bounds = sorted({0, len(text)} | {n["pos"] for n in ns} | {n["pos"] + len(n["quote"]) for n in ns})
        out, started = [], set()
        for a, b in zip(bounds, bounds[1:]):
            seg = text[a:b]
            cover = [n for n in ns if n["pos"] <= a and n["pos"] + len(n["quote"]) >= b]
            if not cover:
                out.append(esc(seg))
                continue
            anchors = ""
            for n in cover:
                if n["id"] not in started:
                    started.add(n["id"])
                    anchors += f'<span class="anchor" id="q-{n["id"]}"></span>'
            out.append(f'{anchors}<mark data-notes="{" ".join(n["id"] for n in cover)}" '
                       f'data-types="{" ".join(n["type"] for n in cover)}">{esc(seg)}</mark>')
        return "".join(out)

    def card(n, gid=None, link=None):
        cls = "note gnote" if gid else "note"
        idattr = f'g-{n["id"]}' if gid else n["id"]
        link = link or n["turn"]
        title = L["jump"]
        return (f'<aside class="{cls}" data-type="{n["type"]}" id="{idattr}" data-nid="{n["id"]}">'
                f'<div class="note-head"><span class="tag">{LABEL[n["type"]]}</span>'
                f'<a class="jump" href="#q-{n["id"]}" title="{title}">{link}</a></div>'
                f'<div class="note-title">{esc(n["title"])}</div>'
                f'<blockquote>„{esc(n["quote"])}”</blockquote><p>{esc(n["text"])}</p></aside>')

    # transcript
    section_at = {s["start"]: (i, s) for i, s in enumerate(rep["sections"])}
    body = []
    for t in turns:
        if t["id"] in section_at:
            i, s = section_at[t["id"]]
            if i:
                body.append("</section>")
            body.append(f'<section class="chunk" id="s{i + 1}"><header class="chunk-head">'
                        f'<div class="chunk-meta">{L["part"]} {i + 1}{" · " + t["ts"] if t.get("ts") else ""}</div>'
                        f'<h2>{esc(s["title"])}</h2><p class="chunk-sum">{esc(s["summary"])}</p></header>')
        sp = speakers[t["sp"]]
        cls = "sp-iv" if sp["role"] == "interviewer" else "sp-ee"
        margin = "".join(card(n) for n in notes_by_turn.get(t["id"], []))
        body.append(f'<div class="row" id="{t["id"]}"><div class="turn {cls}">'
                    f'<div class="who"><span class="name">{esc(sp["name"])}</span>'
                    + (f'<a class="ts" href="#{t["id"]}">{t["ts"]}</a>' if t.get("ts") else "") + '</div>'
                    f'<div class="text">{render_text(t)}</div></div><div class="margin">{margin}</div></div>')
    body.append("</section>")

    filters = "".join(f'<label class="filter" data-type="{k}"><span class="sw"></span>{lbl} '
                      f'<span class="count">{counts[k]}</span></label>' for k, lbl in TYPES if counts[k])
    index_cols = "".join(
        f'<div class="ix-col" data-type="{k}"><h3><span class="dot"></span>{lbl} ({counts[k]})</h3><ul>'
        + "".join(f'<li><a href="#q-{n["id"]}">{esc(n["title"])}</a> <span class="ix-t">{n["turn"]}</span></li>'
                  for n in sorted((n for n in notes if n["type"] == k), key=lambda n: (order[n["turn"]], n["pos"])))
        + "</ul></div>" for k, lbl in TYPES if counts[k])
    toc = "".join(f'<li><a href="#s{i + 1}">{'<span class="toc-ts">' + by_id[s["start"]]["ts"] + '</span>' if by_id[s["start"]].get("ts") else ""}{esc(s["title"])}</a></li>'
                  for i, s in enumerate(rep["sections"]))
    stats = "".join(f'<div class="stat{"" if counts[k] else " zero"}" data-type="{k}"><b>{counts[k]}</b><span>{lbl}</span></div>' for k, lbl in TYPES)
    points = "".join(f"<li>{esc(p)}</li>" for p in rep["summary"]["points"])

    # notes by theme
    type_rank = {k: i for i, k in enumerate(TYPE_KEYS)}
    parts = []
    for p in rep["groups"]["parts"]:
        gh = []
        for gi, g in enumerate(p["groups"]):
            ns = sorted((nmap[x] for x in g["notes"]), key=lambda n: (type_rank[n["type"]], order[n["turn"]]))
            gh.append(f'<div class="grp" id="{p["id"]}-{gi + 1}"><h3>{esc(g["title"])}</h3>'
                      f'<div class="cards">{"".join(card(n, gid=True, link=n["turn"] + " " + L["in_tr"]) for n in ns)}</div></div>')
        parts.append(f'<section class="part" id="part-{p["id"]}"><header class="chunk-head"><h2>{esc(p["title"])}</h2>'
                     f'<p class="chunk-sum">{esc(p.get("intro", ""))}</p></header>{"".join(gh)}</section>')

    # findings
    def chips(ids, lbl):
        if not ids:
            return ""
        c = "".join(f'<a class="chip" data-type="{nmap[s]["type"]}" href="#q-{s}" title="{esc(nmap[s]["title"])}">'
                    f'<span class="dot"></span>{LABEL[nmap[s]["type"]]} · {nmap[s]["turn"]}</a>' for s in ids)
        return f'<div class="chips"><span class="lbl">{lbl}</span>{c}</div>'

    f = rep.get("findings", {})
    hyps = "".join(f'<article class="hyp" data-status="{h["status"]}"><div class="status">{L["status"][h["status"]]}</div>'
                   f'<h3>{esc(h["claim"])}</h3><p>{esc(h.get("comment", ""))}</p>{chips(h.get("evidence", []), L["evidence"])}</article>'
                   for h in f.get("hypotheses", []))
    nqs = "".join(f'<li><div class="q">{esc(q["question"])}</div><p>{esc(q.get("why", ""))}</p>{chips(q.get("sources", []), L["sources"])}</li>'
                  for q in f.get("next_questions", []))
    caveat = f'<div class="caveat">{esc(f["caveat"])}</div>' if f.get("caveat") else ""

    sub_bits = [meta.get("date", "")]
    if meta.get("duration_min"):
        sub_bits.append(f'{round(meta["duration_min"])} {L["min"]}')
    sub_bits.append(", ".join(esc(s["name"]) for s in speakers.values()))
    sub_bits += [f'{len(turns)} {L["turns"]}', f'{len(notes)} {L["notes"]}']
    sub = " · ".join(b for b in sub_bits if b)

    tab_keys = ["overview", "transcript", "themes", "findings"]
    tabbar = "".join(f'<button class="tab" role="tab" data-tab="{k}">{lbl}</button>' for k, lbl in zip(tab_keys, L["tabs"]))
    store = "dir-" + "".join(ch for ch in meta["title"] if ch.isalnum())[:40]
    js = (HERE / "report.js").read_text().replace("__TYPES__", json.dumps(TYPE_KEYS)).replace("__STORE__", json.dumps(store))

    return f"""<!doctype html>
<html lang="{meta['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(meta['title'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&display=swap" rel="stylesheet"><style>{CSS_PATH.read_text()}</style></head><body>
<header class="top"><div class="wrap"><div class="eyebrow">{esc(meta.get('eyebrow', ''))}</div>
<h1 class="title">{esc(meta['title'])}</h1><p class="sub">{sub}</p></div></header>
<nav class="tabs"><div class="wrap" role="tablist">{tabbar}</div></nav>
<nav class="bar"><div class="wrap"><span class="lbl">{L['show']}</span>{filters}
<button class="btn" id="all">{L['all']}</button><button class="btn" id="none">{L['none']}</button></div></nav>

<section class="panel" id="tab-overview"><div class="wrap">
<h2 class="lead">{esc(rep['summary']['headline'])}</h2>
<ul class="points">{points}</ul>
<div class="stats">{stats}</div>
<h3 class="sect">{L['topics']} ({len(rep['sections'])})</h3><ol class="toc">{toc}</ol>
</div></section>

<section class="panel" id="tab-transcript"><main class="wrap transcript">{''.join(body)}<div class="notes-layer"></div></main></section>

<section class="panel" id="tab-themes"><div class="wrap">
<h2 class="lead">{esc(rep['groups']['headline'])}</h2>
<details class="box"><summary>{L['by_type']}</summary><div class="index">{index_cols}</div></details>
{''.join(parts)}</div></section>

<section class="panel" id="tab-findings"><div class="wrap">
<h2 class="lead">{esc(f.get('headline', ''))}</h2>{caveat}
<h3 class="sect">{L['hyp']}</h3><div class="hyps">{hyps}</div>
<h3 class="sect">{L['next']}</h3><ol class="nq">{nqs}</ol>
</div></section>

<footer class="wrap">{esc(meta.get('footer', L['footer']))}</footer>
<script>{js}</script></body></html>"""


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
