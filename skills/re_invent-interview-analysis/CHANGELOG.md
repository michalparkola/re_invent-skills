# Changelog

Versions use the release date (YYYY-MM-DD). A second release on the same day adds `.2`, `.3` and so on. Add a new entry at the top for each change. Put the same date in the `metadata.version` field of `SKILL.md`.

## 2026-11-12.3
Mobile tab bar fix.
- Under 500 px the tabs wrap to 2 rows. All 4 tabs show without a sideways scroll.
- The transcript filter bar sits below the tab bar at any tab bar height (`--tabs-h`, set by `syncBars()` in `report.js`). Anchor jumps use the same offset.
- 26 tests.

## 2026-11-12.2
Layout changes based on Refactoring UI.
- Type scale: 12, 14, 16, 20, 24, 30, 36, 48 px. No other font sizes.
- Line length: prose 65 to 70ch, headings 40 to 60ch.
- Fewer borders: notes, stats, hypotheses and the type index use a soft background and a colored left or top edge. The tab bar has one line.
- More space between groups than inside them: sections 48 px, groups 32 px, cards 12 px.
- "All" and "None" filter buttons are secondary (outline).
- Stats with 0 notes are grey.
- Section labels ("Hypotheses", "Topics") are grey. Theme part headings are larger than group headings.
- 25 tests.

## 2026-11-12
First version.
- Input: a transcript as plain `Name: text` lines, `**HH:MM:SS — Name**` headings or JSON segments. Timestamps are optional.
- Output: one HTML file with 4 tabs: overview, transcript with margin notes, notes by theme, findings.
- 7 note types. Interviewee: job, pain, workaround, signal. Interviewer: good move, distortion, missed opportunity. Based on The Mom Test, Jobs to be Done and Clean Language.
- The build script checks quotes, speakers, groups, findings and em dashes, and writes nothing on error.
- Styles follow reinvent.michalparkola.com.
- 20 tests.
