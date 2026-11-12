# Data format

Two input files go into `scripts/build_report.py`. The script validates them and puts `{"turns": [...], "report": {...}}` into the `report-data` tag of `assets/report.html`. Without Python, you put the same object there yourself.

## turns.json

Made by `scripts/prepare_turns.py`. Do not edit wording.

```json
[{"id": "t1", "sp": "A", "ts": "00:00:05", "text": "..."}]
```

`ts` is `""` when the transcript has no timestamps. The page then hides times.

## report.json

All copy is in the transcript language (`meta.lang`: `pl` or `en`; the UI labels follow it). No em dashes anywhere.

```json
{
 "meta": {
  "title": "Jan, wywiad 1",                 // page and tab title: "<Name>, <what>"
  "eyebrow": "Discovery · <product or project>",
  "date": "12 listopada 2026",              // written out in the transcript language
  "duration_min": 47,
  "lang": "pl",
  "speakers": {                              // every sp code in turns.json
   "A": {"name": "Anna", "role": "interviewer"},
   "J": {"name": "Jan", "role": "interviewee"}
  },
  "footer": "optional override of the default footer"
 },
 "summary": {
  "headline": "One sentence that states the main conclusion",
  "points": ["3 to 6 sentences, each a concrete finding with a fact or number"]
 },
 "sections": [                               // first section starts at the first turn; transcript order
  {"start": "t1", "title": "Heading that states the point of the chunk", "summary": "One or two sentences."}
 ],
 "notes": [
  {"id": "n1", "type": "pain", "turn": "t4",
   "quote": "exact substring of turn t4",
   "title": "Short conclusion",
   "text": "What it shows, how strong the evidence is; for distortion or missed: the better question."}
 ],
 "groups": {
  "headline": "Conclusion across all groups",
  "parts": [
   {"id": "interviewee", "title": "Jan: zadania, problemy, rozwiązania, sygnały", "intro": "...",
    "groups": [{"title": "Heading that states the theme's conclusion", "notes": ["n2", "n5"]}]},
   {"id": "interviewer", "title": "Prowadzenie wywiadu", "intro": "...",
    "groups": [{"title": "Pattern and its effect", "notes": ["n1", "n4"]}]}
  ]
 },
 "findings": {
  "headline": "What the call proves and what it leaves open",
  "caveat": "Optional: sample size, privacy, bias.",
  "hypotheses": [
   {"claim": "Testable statement", "status": "supported|contradicted|open",
    "comment": "Why this status; name the strength of the evidence.", "evidence": ["n5"]}
  ],
  "next_questions": [
   {"question": "Clean, past-focused question", "why": "What it tests", "sources": ["n6"]}
  ]
 }
}
```

(The `//` comments above are for reading only. JSON files must not contain them.)

## Rules the build script checks

- Each `quote` is an exact substring of its turn.
- `job`, `pain`, `workaround`, `signal` quote an interviewee turn. `play-good` and `play-distort` quote an interviewer turn. `play-missed` may quote either.
- Note ids are unique. Each note sits in exactly one group. Evidence notes go in part `interviewee`, interviewer notes in part `interviewer`.
- Hypothesis and question sources point to existing notes. Hypothesis status is one of the three values.
- Sections start at the first turn and follow transcript order.
- No em dash (U+2014) in report.json.

On any failure the script prints every problem and writes nothing.
