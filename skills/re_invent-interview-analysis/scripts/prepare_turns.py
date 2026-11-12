#!/usr/bin/env python3
"""Turn a transcript into turns.json: [{id, sp, ts, text}].

Input formats (detected in this order):
  - JSON: a list of segments [{"speaker", "text", "start"?}], or an object whose
    first list value is that list. "start" is seconds (number) or "H:MM:SS".
  - Markdown headings, text below each one:
        **00:00:44 — Full Name**
  - Plain lines "Name: text", with an optional timestamp before the name:
        [00:00:44] Name: text      00:00:44 - Name: text      Name: text
    A line without "Name:" continues the previous turn.

Timestamps are optional; turns without one get ts "". Consecutive blocks of one
speaker merge into one turn. Wording stays as it is; only whitespace and stray
spaces before punctuation are cleaned.

Usage:
  prepare_turns.py INPUT OUT.json [--speaker "Full Name=CODE" ...]
Speakers without a mapping get the first letter of their name (two letters on a clash).
"Unassigned" or "Unknown" lines go to the previous speaker.
"""
import argparse, json, re, sys
from pathlib import Path

CLOCK = r"\d{1,2}:\d{2}(?::\d{2})?"
MD_HEAD = re.compile(rf"^\*\*({CLOCK})\s*[—–-]\s*(.+?)\*\*\s*$", re.M)
LINE = re.compile(rf"^\s*(?:[\[(]?({CLOCK})[\])]?\s*[—–-]?\s*)?"
                  r"([^\W\d][\w.'’ -]{0,40}?)\s*:\s+(.*\S)\s*$")
HINT = ("No speakers found. Give the transcript as '**HH:MM:SS — Name**' headings, "
        "'Name: text' lines (optional timestamp first), or a JSON list of "
        "{speaker, text, start} segments.")


def norm_ts(ts):
    if ts is None or ts == "":
        return ""
    if isinstance(ts, (int, float)):
        s = int(ts)
        return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"
    parts = [int(x) for x in str(ts).split(":")]
    while len(parts) < 3:
        parts.insert(0, 0)
    h, m, s = parts
    return f"{h:02d}:{m:02d}:{s:02d}"


def read_json(raw):
    data = json.loads(raw)
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return [((l.get("speaker") or l.get("name") or "Unassigned").strip(), norm_ts(l.get("start")), l.get("text", ""))
            for l in data]


def read_markdown(raw, heads):
    blocks = []
    for h, nxt in zip(heads, heads[1:] + [None]):
        body = raw[h.end(): nxt.start() if nxt else len(raw)]
        blocks.append((h.group(2).strip(), norm_ts(h.group(1)), body))
    return blocks


def read_lines(raw):
    blocks = []
    for line in raw.splitlines():
        m = LINE.match(line)
        if m:
            blocks.append((m.group(2).strip(), norm_ts(m.group(1)), m.group(3)))
        elif line.strip() and blocks:
            blocks[-1] = (blocks[-1][0], blocks[-1][1], blocks[-1][2] + " " + line)
    return blocks


def read_blocks(path):
    raw = Path(path).read_text()
    if raw.lstrip()[:1] in "[{":
        try:
            return read_json(raw)
        except (json.JSONDecodeError, AttributeError):
            pass
    heads = list(MD_HEAD.finditer(raw))
    blocks = read_markdown(raw, heads) if heads else read_lines(raw)
    if not blocks:
        sys.exit(HINT)
    return blocks


def join(parts):
    s = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if re.fullmatch(r"[,.;:!?]+", p):
            s = s.rstrip() + p
            continue
        s = f"{s} {p}" if s else p
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"^[,.;:]\s*", "", s)
    return s.strip()


def codes_for(names, given):
    codes, used = {}, set(given.values())
    for n in names:
        if n in given:
            codes[n] = given[n]
            continue
        letters = re.sub(r"[^\w]", "", n)
        for k in (1, 2, 3):
            c = letters[:k].upper()
            if c and c not in used:
                break
        codes[n] = c
        used.add(c)
    return codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--speaker", action="append", default=[], help='"Full Name=CODE"')
    a = ap.parse_args()
    given = dict(s.split("=", 1) for s in a.speaker)

    turns = []
    for name, ts, text in read_blocks(a.input):
        if name.lower() in ("unassigned", "unknown", ""):
            name = turns[-1]["name"] if turns else None
        if turns and turns[-1]["name"] == name:
            turns[-1]["parts"].append(text)
        else:
            turns.append({"name": name, "ts": ts, "parts": [text]})
    if turns and turns[0]["name"] is None:
        nxt = next((t["name"] for t in turns if t["name"]), "Unknown")
        turns[0]["name"] = nxt

    names = list(dict.fromkeys(t["name"] for t in turns))
    codes = codes_for(names, given)
    out = []
    for t in turns:
        text = join(t["parts"])
        if not text:
            continue
        if out and out[-1]["sp"] == codes[t["name"]]:
            out[-1]["text"] = join([out[-1]["text"], text])
            continue
        out.append({"id": f"t{len(out) + 1}", "sp": codes[t["name"]], "ts": t["ts"], "text": text})
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{len(out)} turns -> {a.out}")
    for n in names:
        print(f"  {codes[n]} = {n} ({sum(1 for t in out if t['sp'] == codes[n])} turns)")


if __name__ == "__main__":
    main()
