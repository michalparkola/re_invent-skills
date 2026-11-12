# re_invent-skills

Skille dla agentów AI (Claude Code, Codex i podobnych), które wspierają pracę w programie re_invent. Każdy skill to folder z instrukcją `SKILL.md`, skryptami i testami. Agent czyta instrukcję i wykonuje powtarzalną część pracy, a Ty skupiasz się na wnioskach.

## Program re_invent

[re_invent](https://reinvent.michalparkola.com) to 3-miesięczny program coachingowo-warsztatowy Michała Parkoły dla technicznych founderów małych i średnich firm software i AI. Uczestnicy prowadzą około 60 rozmów z potencjalnymi klientami, szukają powtarzających się problemów i na tej bazie budują ofertę, którą mogą skalować.

## Skille

### re_invent-interview-analysis

Zamienia transkrypt rozmowy odkrywczej w jeden samodzielny raport HTML. Raport ma 4 zakładki:

1. **Przegląd**: główny wniosek, kluczowe punkty, liczba notatek według typu, lista tematów.
2. **Transkrypt**: tekst w tematycznych częściach z notatkami na marginesie przy dokładnych cytatach.
3. **Notatki według tematów**: dowody rozmówcy pogrupowane według tematów, ruchy prowadzącego według wzorców.
4. **Wnioski**: hipotezy (potwierdzona, obalona, otwarta) z dowodami i pytania na następną rozmowę.

Typy notatek: zadanie, problem, obecne rozwiązanie, sygnał (rozmówca) oraz dobry ruch, zniekształcenie, przegapiona okazja (prowadzący). Metoda opiera się na The Mom Test, Jobs to be Done i Clean Language.

Raport działa offline i zostaje na Twoim dysku. Skill nie pobiera danych z innych systemów.

#### Instalacja

```bash
git clone https://github.com/michalparkola/re_invent-skills.git ~/Projects/re_invent-skills
ln -s ~/Projects/re_invent-skills/skills/re_invent-interview-analysis ~/.claude/skills/re_invent-interview-analysis
```

Skrypty wymagają tylko Pythona 3 (biblioteka standardowa).

#### Użycie

Daj agentowi transkrypt i poproś o analizę, na przykład:

> Przeanalizuj rozmowę z pliku `rozmowa.txt`. Prowadzę ja (Anna), rozmówca to Jan. Celem było sprawdzić, jak Jan zamyka miesiąc w firmie.

Agent:

1. Zamienia transkrypt na tury (`scripts/prepare_turns.py`). Obsługuje SRT i VTT z imionami mówców (Zoom, Teams, Meet, MacWhisper), eksporty Otter i Fireflies, linie `Imię: tekst`, nagłówki `**HH:MM:SS — Imię**` i segmenty JSON. Inne formaty opisuje `references/input-formats.md`. Znaczniki czasu są opcjonalne.
2. Czyta całą rozmowę, dzieli ją na tematy i pisze notatki z cytatami.
3. Buduje raport (`scripts/build_report.py`) i sprawdza, czy każdy cytat pasuje do transkryptu.

Wynik: plik `report.html` w folderze roboczym. Otwórz go w przeglądarce.

#### Testy

```bash
python3 -m unittest discover -s skills/re_invent-interview-analysis/tests
```

#### Wersje

Wersja to data wydania (`2026-11-12.4`). Historia zmian: [CHANGELOG.md](skills/re_invent-interview-analysis/CHANGELOG.md).
