---
name: re_invent-interview-analysis
description: Turn a discovery interview transcript into a self-contained HTML report. The report has a transcript split into topic chunks, margin notes linked to exact quotes (jobs, pains, workarounds, signals; the interviewer's good moves, distortions and missed follow-ups), notes grouped by theme, and findings with hypotheses and next questions. The method draws on The Mom Test, Jobs to be Done and Clean Language. Use when the user asks to analyze, review or annotate a discovery interview, customer interview, user research call, sales discovery call or problem interview. Polish triggers include "przeanalizuj rozmowę", "analiza wywiadu" and "raport z rozmowy odkrywczej".
metadata:
  version: "2026-11-12.5"
---

# Discovery interview report

Version 2026-11-12.5. See `CHANGELOG.md`.

The output is one self-contained HTML page with four tabs:

1. **Overview**: headline, key points, note counts by type, topic list with timestamps.
2. **Transcript**: the full transcript in topic chunks. The chunk headings state each chunk's point. Margin notes sit next to highlighted exact quotes and never overlap. Filters work by note type.
3. **Notes by theme**: an index of all notes by type at the top. Below it, the interviewee's evidence grouped by theme and the interviewer's moves grouped by pattern.
4. **Findings**: hypotheses marked supported, contradicted or open, each linked to its evidence. Next questions for the next interview.

The page has light and dark mode, a mobile layout, a title, and details in the subtitle.

Read `references/taxonomy.md` before you write notes. Read `references/data-format.md` before you write `report.json`.

## Workflow

### 1. Take the transcript and context
- Input: a transcript the user or the calling agent gives you. Do not fetch it from other systems.
- `prepare_turns.py` reads these formats and detects the format itself:
  - SRT or WebVTT subtitles with speaker names (Zoom, Teams, Meet, Whisper tools).
  - Header blocks: a line with a name and a time, the text below (Otter, Fireflies, tl;dv).
  - Markdown headings `**HH:MM:SS — Name**` with the text below each one.
  - Plain lines `Name: text`, with an optional timestamp before the name.
  - A JSON list of segments `{"speaker", "text", "start"}`.
- If the script refuses the input, read `references/input-formats.md`. It shows each format and how to convert others (DOCX, PDF, tables, subtitles without speakers).
- Establish who is the interviewer and who is the interviewee. Use the context you have or the content. Ask the user only if it is unclear.
- Find the goal of the interview and the hypotheses it tested. Take them from the user's message or the call opening. If none are stated, infer them from the interviewer's questions and say so in the findings caveat.
- Put the work files where the user's or project's rules say. Otherwise, use a new folder next to the transcript.

### 2. Prepare turns
The scripts need Python 3 and only its standard library. `<skill>` is the folder of this file.
```bash
python3 <skill>/scripts/prepare_turns.py transcript.txt turns.json --speaker "Anna Nowak=A" --speaker "Jan Kowalski=J"
```
- Check the speaker list that the script prints. "Unassigned" or "Unknown" lines go to the previous speaker. A wrong name in the list means a line with a colon was read as a speaker; fix the input.
- Do not change the wording. Transcription errors stay as they are, so that the quotes match.

### 3. Read the whole transcript
- Read all of turns.json. For long calls, read it in slices. Do not sample.
- Mark topic shifts. Aim for one section per 3 to 8 minutes.

### 4. Write report.json in the transcript language
Do the work in this order. Long calls can go section by section.
1. `sections`: a heading that states the point of the chunk (a conclusion, not a label), plus one or two summary sentences.
2. `notes`: follow `references/taxonomy.md`. Copy each quote character for character from turns.json. Give ids n1, n2, ... in transcript order.
3. `groups`:
   - Interviewee part: group by theme, for example one area of the job or one problem.
   - Interviewer part: group by pattern, for example "past-specific questions", "early pitch", "unprobed numbers".
   - Every heading states a conclusion.
4. `findings`:
   - Hypotheses with an honest status. Only past facts and commitment count as support. Opinions and hypotheticals leave a hypothesis open.
   - 3 to 8 next questions. Each one is clean and past-focused, and links to the note that prompted it.
5. `summary`: a headline with the main conclusion, plus 3 to 6 points. Each point is a concrete finding.
6. `meta`: the title "<Interviewee>, <interview n or topic>", an eyebrow such as "Discovery · <project>", a written-out date, the duration and the speakers with roles.

### 5. Build and fix
```bash
python3 <skill>/scripts/build_report.py --turns turns.json --report report.json --out "<Title>.html"
```
The script lists every problem and writes nothing until all checks pass. Fix the data. Do not loosen the checks. Then it copies `assets/report.html` with the data in it.

#### Without Python
Use this mode when you cannot run scripts. The template gives the same page.
1. Write turns.json by hand from the transcript. Copy the wording exactly. Use the turn format in `references/data-format.md`.
2. Copy `assets/report.html` to `<Title>.html`.
3. Replace `null` in `<script type="application/json" id="report-data">null</script>` with `{"turns": [...], "report": {...}}`. Write `<` in the JSON as `\u003c`.
4. Open the page. The page shows a red box when a quote does not match its turn, a turn is missing or a note type is wrong. It hides those notes. Fix the data until the box goes away.
The page does not do the other checks of the script (groups, roles, statuses, em dashes). Check them yourself against `references/data-format.md`.

If you cannot write files at all, give the report as Markdown in the chat: summary, sections with notes and quotes, groups, findings.

### 6. Edit pass on all generated copy
Apply this to the headings, summaries, notes, groups and findings. Do not apply it to the transcript or the quotes. Check that:
- There are no adverbs and no filler such as "warto zauważyć", "kluczowe", "w gruncie rzeczy", "it's worth noting" or "crucially".
- There are no "not X but Y" contrasts. State Y.
- Each sentence uses active voice with a person as the subject.
- Each statement names the specific thing, number or episode. There are no vague declaratives.
- There are no em dashes, no throat-clearing openers and no quotable one-liners.
- Each heading states a conclusion that a reader can act on.
Rebuild after the edits.

### 7. Verify in a browser
Open the HTML and run this check at a width of 1280 px. Expect `ov: 0`, `headRight < noteLeft` and `hscroll: false`. Then check 375 px for horizontal scroll on every tab.
```js
document.querySelector('[data-tab=transcript]').click();
await new Promise(r=>setTimeout(r,300));
const ns=[...document.querySelectorAll('.notes-layer .note:not(.hidden)')].map(n=>n.getBoundingClientRect()).sort((a,b)=>a.top-b.top);
let ov=0;for(let i=1;i<ns.length;i++)if(ns[i].top<ns[i-1].bottom-0.5)ov++;
({notes:ns.length,ov,headRight:Math.max(...[...document.querySelectorAll('.chunk h2')].map(h=>h.getBoundingClientRect().right)),noteLeft:Math.min(...ns.map(r=>r.left)),hscroll:document.documentElement.scrollWidth>innerWidth})
```

### 8. Deliver
- Keep the report local. Interview data is private. Do not publish it, upload it or share it unless the user asks.
- Report to the user:
  - The path.
  - The headline.
  - The note counts by type.
  - The 2 or 3 most important distortions or missed opportunities.
  - Which hypotheses changed status.

## Files
- `scripts/prepare_turns.py`: transcript (SRT, WebVTT, header blocks, markdown headings, plain lines or JSON segments) to turns.json.
- `references/input-formats.md`: the input formats with samples, and how to convert other formats.
- `assets/report.html`: the report template. It holds the styles, the UI labels and the renderer. It is the only source of the page look.
- `scripts/build_report.py`: validates the data and puts it into the template.
- `references/taxonomy.md`: the note types and the judgment rules.
- `references/data-format.md`: the report.json contract and the checks.
- `tests/test_scripts.py`: run `python3 tests/test_scripts.py` after you change a script or the template. The renderer tests need Node.js and skip without it.
