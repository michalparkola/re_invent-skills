# Note taxonomy

Seven note types. Four record what the interviewee said (evidence). Three judge how the interviewer ran the call.
Sources: The Mom Test (Rob Fitzpatrick), Jobs to be Done (switch interviews, forces of progress), Clean Language (David Grove).

The build script enforces the speaker rule in the third column.

| key | PL label | EN label | Quote from | Records |
|---|---|---|---|---|
| `job` | Zadanie | Job | interviewee | The progress the person tries to make in a specific situation |
| `pain` | Problem | Pain | interviewee | A struggle, its cost and its consequences |
| `workaround` | Obecne rozwiązanie | Current workaround | interviewee | What the person does now or did before |
| `signal` | Sygnał | Signal | interviewee | Evidence of priority or commitment, or its absence |
| `play-good` | Dobry ruch | Good move | interviewer | A move that got clean, specific, past evidence |
| `play-distort` | Zniekształcenie | Distortion | interviewer | A move that bent the data toward the interviewer's ideas |
| `play-missed` | Utracona okazja | Missed opportunity | either | A cue the interviewer did not follow up |

## Evidence notes (interviewee's own words)

The quote must be the interviewee's words. Never put a paraphrase by the interviewer in an evidence note: if the interviewee only agreed with the interviewer's framing ("tak, dokładnie"), that is weak evidence, and often a `play-distort` note on the interviewer's turn.

In each evidence note, say how strong the evidence is. Strong: a specific past episode, a number, money or time spent, an action taken. Weak: an opinion, a generalization ("zawsze", "zwykle"), a hypothetical ("kupiłbym"), a compliment.

### job
- JTBD frame: "Kiedy [sytuacja], chcę [postęp], żeby [rezultat]." Write the title in that spirit, in the interviewee's terms.
- Include the trigger (what happened that made the person act), and functional, emotional or social sides when the transcript shows them.
- A feature request is not a job. Ask what the feature would let them do, and record that, if the transcript has it.

### pain
- Name the struggle and its cost: hours, money, missed deadlines, conflict, stress.
- Prefer a specific episode over a general complaint. If only a general complaint exists, say so in the note.

### workaround
- Tools, spreadsheets, people, paid services, manual steps, or doing nothing (non-consumption).
- Past switches and what triggered them. JTBD forces: push of the current situation, pull of the new solution, anxiety about the new, habit of the present.
- A workaround with real effort or money is strong evidence the pain matters.

### signal
- Positive: money or time already spent, an active search for a solution, a home-built fix, a strong emotion tied to an episode, an offer of a next step (intro, pilot, data, another meeting, pre-payment). Mom Test: commitment and advancement.
- Negative or empty: "fajny pomysł", "na pewno bym kupił", polite interest without a next step, "never looked for a solution". Record these too, and call them weak or zero signal in the note.

## Interviewer notes

Judge each move by one question: did it get the interviewee to give specific facts from their own life, in their own words?

### play-good
- Asks about the last time or a specific episode ("Opowiedz o ostatnim razie, kiedy…").
- Asks for numbers, cost, frequency, who else was involved.
- Follows a vague or loaded word with a clean question in the interviewee's words: "Jakie [X]?", "Co jeszcze o [X]?", "Co się dzieje tuż przed [X]?", "Skąd wiesz, że [X]?".
- Asks what they tried, why that failed, what they pay now.
- Leaves silence; lets the interviewee correct a summary.
- Deflects a compliment back to facts. Asks for a concrete next step at the end.
- A used opportunity: the interviewer catches a cue (emotion, number, workaround) and digs. Name the cue in the note.

### play-distort
- Leading question that contains the expected answer ("Czy to nie frustrujące, że…?").
- Hypothetical or future question ("Czy byś kupił…", "Ile byś zapłacił…").
- Pitch: describes the interviewer's solution before the problem is clear, or asks for an opinion on the idea.
- Fishing for compliments or validation.
- Imports the interviewer's own label, metaphor or category and then treats the interviewee's "tak" as data. Clean Language: the interviewer adds content.
- Paraphrase that changes meaning, stacked questions, answering their own question, arguing, coaching or advising during discovery.
- In the note, quote the move, name the pattern, and write a clean alternative question in the transcript language.

### play-missed
- The interviewee gives a cue and the interviewer moves on: an emotional word, a number, money, a workaround, a past attempt, a third person (boss, client, partner), a contradiction, "zawsze/nigdy", a vague abstraction.
- The interviewer accepts fluff ("tak, to byłoby super") without asking for a past example.
- The call ends without asking for a next step.
- Quote the cue (often the interviewee's words). In the note, write the follow-up question that would have worked.

## Density and balance

- About one note for every 4 to 6 turns. A 60 minute call usually gets 50 to 90 notes.
- Cover every section. Do not stack many notes on one sentence; two notes on the same quote are fine when they show two types (for example `pain` and `play-missed`).
- Be fair to the interviewer: record good moves with the same care as distortions.
- Quotes: the shortest exact span that carries the point, usually 3 to 20 words. Copy them from turns.json, not from memory.
