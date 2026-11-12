# Input formats

`prepare_turns.py` detects the format. Timestamps are optional in every format. Consecutive parts by one speaker merge into one turn. The script prints the speaker list: check it before you go on.

## Supported formats

### WebVTT (`.vtt`): Zoom, Microsoft Teams, Google Meet
The speaker is in a `<v Name>` tag (Teams) or as `Name:` at the start of the cue (Zoom).
```
WEBVTT

1
00:00:02.100 --> 00:00:04.000
<v Anna Nowak>Tell me about the last time you closed the month.</v>
```

### SRT (`.srt`): MacWhisper, Descript, other Whisper tools
Export with speaker labels. The speaker is `Name:` or `[Name]` at the start of the cue. A cue without a speaker continues the previous speaker.
```
1
00:00:01,400 --> 00:00:04,000
Anna: Tell me about the last time you closed the month.
```

### Header blocks: Otter, Fireflies, tl;dv
A line with a name and a time (in either order), then the text on the next lines.
```
Anna Nowak  0:03
Tell me about the last time you closed the month.

Jan Kowalski - 00:09
In March. It took three nights.
```

### Markdown headings
```
**00:00:44 — Anna Nowak**

Tell me about the last time you closed the month.
```

### Plain lines
`Name: text`, with an optional timestamp first: `[00:00:44] Anna: text`, `00:00:44 - Anna: text`. A line without `Name:` continues the previous turn.

### JSON segments
A list of `{"speaker", "text", "start"}`, or an object whose first list value is that list. `start` is seconds or `H:MM:SS`.

## Other formats: convert to plain lines
Convert the input to `Name: text` lines, one turn per line. Keep the wording as it is, so that the quotes match. Then run the script on the result.

- **DOCX (Teams, Word)**: extract the text, for example with `textutil -convert txt file.docx` on macOS or `pandoc file.docx -t plain`. Then check which format the text has.
- **PDF**: extract the text with `pdftotext -layout file.pdf`. Remove page headers and page numbers.
- **Tables (CSV, XLSX)**: write one line per row: `Speaker: Text`. Put the start time first if the table has one: `[00:01:05] Speaker: Text`.
- **Chat logs or notes**: use `Name: text` lines. Notes without the exact words give weak quotes. Tell the user.

## Subtitles or text without speakers
The analysis needs to know who said what. The script refuses subtitles with no speaker names. Do not guess the speakers. Ask the user to:
1. Export again with speaker labels. MacWhisper, Descript, Otter, Zoom and Teams can do this.
2. Or add `Name:` at the start of each turn by hand.
