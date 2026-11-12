#!/usr/bin/env python3
"""Tests for prepare_turns.py and build_report.py. Run: python3 tests/test_scripts.py"""
import copy, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
PREP = ROOT / "scripts" / "prepare_turns.py"
BUILD = ROOT / "scripts" / "build_report.py"


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


class PrepareTurns(unittest.TestCase):
    def test_markdown_merges_same_speaker_and_maps_codes(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "turns.json"
            r = run(PREP, FIX / "transcript.md", out, "--speaker", "Anna Nowak=A", "--speaker", "Jan Kowalski=J")
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            turns = json.loads(out.read_text())
            self.assertEqual(len(turns), 6)
            self.assertEqual(turns[1], {"id": "t2", "sp": "J", "ts": "00:00:07", "text": "Tak. Słychać dobrze."})
            self.assertEqual(turns[0]["sp"], "A")
            self.assertEqual([t["id"] for t in turns], [f"t{i}" for i in range(1, 7)])

    def test_unknown_speaker_gets_initial_and_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "turns.json"
            r = run(PREP, FIX / "transcript.md", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            turns = json.loads(out.read_text())
            self.assertEqual({t["sp"] for t in turns}, {"A", "J"})
            self.assertIn("Anna Nowak", r.stdout)

    def prep(self, name, content):
        d = Path(tempfile.mkdtemp())
        p = d / name; p.write_text(content)
        out = d / "turns.json"
        r = run(PREP, p, out)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return json.loads(out.read_text())

    def test_json_segments_with_seconds_or_clock(self):
        src = [
            {"speaker": "Anna", "text": "Opowiedz", "start": 1.4},
            {"speaker": "Anna", "text": "o marcu .", "start": 2},
            {"speaker": "Jan", "text": "Dobrze.", "start": "0:01:05"},
        ]
        turns = self.prep("in.json", json.dumps(src))
        self.assertEqual(turns[0]["text"], "Opowiedz o marcu.")
        self.assertEqual(turns[0]["ts"], "00:00:01")
        self.assertEqual(turns[1]["ts"], "00:01:05")
        self.assertEqual(len(turns), 2)

    def test_plain_lines_with_timestamps(self):
        txt = ("[00:00:03] Anna: Opowiedz o ostatnim zamknięciu.\n"
               "00:00:09 - Jan: W marcu.\n"
               "Trwało tydzień.\n\n"
               "(0:00:20) Anna: Ile dni?\n")
        turns = self.prep("t.txt", txt)
        self.assertEqual([(t["sp"], t["ts"], t["text"]) for t in turns], [
            ("A", "00:00:03", "Opowiedz o ostatnim zamknięciu."),
            ("J", "00:00:09", "W marcu. Trwało tydzień."),
            ("A", "00:00:20", "Ile dni?")])

    def test_plain_lines_without_timestamps(self):
        turns = self.prep("t.txt", "Anna: Jak to wyglądało?\nJan: Ręcznie, w Excelu.\nJan: Co miesiąc.\n")
        self.assertEqual([(t["sp"], t["ts"], t["text"]) for t in turns], [
            ("A", "", "Jak to wyglądało?"), ("J", "", "Ręcznie, w Excelu. Co miesiąc.")])

    def test_unrecognized_format_fails_with_hint(self):
        d = Path(tempfile.mkdtemp()); p = d / "t.txt"; p.write_text("just prose with no speakers at all")
        r = run(PREP, p, d / "o.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Name:", r.stdout + r.stderr)


class BuildReport(unittest.TestCase):
    def build(self, mutate=None, turns=None):
        rep = json.loads((FIX / "report.json").read_text())
        if mutate:
            mutate(rep)
        d = tempfile.mkdtemp()
        rp = Path(d) / "report.json"; rp.write_text(json.dumps(rep, ensure_ascii=False))
        out = Path(d) / "out.html"
        tp = FIX / "turns.json"
        if turns is not None:
            tp = Path(d) / "turns.json"; tp.write_text(json.dumps(turns, ensure_ascii=False))
        r = run(BUILD, "--turns", tp, "--report", rp, "--out", out)
        return r, out

    def test_valid_report_builds_one_tabbed_page(self):
        r, out = self.build()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = out.read_text()
        self.assertIn('<html lang="pl">', html)
        self.assertIn("<title>Jan, wywiad 1</title>", html)
        for tab in ["overview", "transcript", "themes", "findings"]:
            self.assertIn(f'id="tab-{tab}"', html)
        self.assertEqual(html.count("<aside class=\"note\""), 7)
        self.assertEqual(len(set(re.findall(r'id="q-(n\d+)"', html))), 7)
        self.assertIn("Utracona okazja", html)
        self.assertIn("Zniekształcenie", html)
        self.assertNotIn("Lekcja", html)
        # type index sits before the first theme group
        themes = html[html.index('id="tab-themes"'):]
        self.assertLess(themes.index('class="index"'), themes.index('class="grp"'))
        # no duplicate element ids
        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)), [i for i in ids if ids.count(i) > 1])

    def test_english_labels(self):
        r, out = self.build(lambda rep: rep["meta"].update(lang="en"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("Missed opportunity", out.read_text())

    def fails_with(self, mutate, needle):
        r, out = self.build(mutate)
        self.assertNotEqual(r.returncode, 0, "build should fail")
        self.assertIn(needle, r.stdout + r.stderr)
        self.assertFalse(out.exists())

    def test_quote_must_be_exact(self):
        self.fails_with(lambda rep: rep["notes"][1].update(quote="siedziałem trzy noce"), "quote not found")

    def test_evidence_must_be_interviewee_words(self):
        self.fails_with(lambda rep: rep["notes"][1].update(turn="t3", quote="ostatnim razie"), "interviewee turn")

    def test_distortion_must_be_interviewer_words(self):
        self.fails_with(lambda rep: rep["notes"][3].update(turn="t6", quote="Pewnie tak."), "interviewer turn")

    def test_lesson_type_rejected(self):
        self.fails_with(lambda rep: rep["notes"][0].update(type="lesson"), "bad type")

    def test_each_note_in_one_group(self):
        def m(rep):
            rep["groups"]["parts"][0]["groups"][0]["notes"].remove("n5")
        self.fails_with(m, "not in any group")

    def test_note_in_wrong_part(self):
        def m(rep):
            rep["groups"]["parts"][0]["groups"][0]["notes"].append("n1")
            rep["groups"]["parts"][1]["groups"][0]["notes"].remove("n1")
        self.fails_with(m, "part interviewee")

    def test_em_dash_rejected(self):
        self.fails_with(lambda rep: rep["summary"].update(headline="Jan — płaci"), "em dash")

    def test_finding_sources_must_exist(self):
        self.fails_with(lambda rep: rep["findings"]["hypotheses"][0].update(evidence=["n99"]), "n99")

    def test_hypothesis_status(self):
        self.fails_with(lambda rep: rep["findings"]["hypotheses"][0].update(status="maybe"), "status")

    def test_sections_start_at_first_turn(self):
        self.fails_with(lambda rep: rep["sections"].pop(0), "first turn")

    def test_reinvent_brand_styles(self):
        r, out = self.build()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = out.read_text()
        self.assertIn("fonts.googleapis.com/css2?family=Oswald", html)
        for token in ["--bg:#fefdfc", "--fg:#2a3139", "--accent:#be4400", "--line:#dee2e5"]:
            self.assertIn(token, html)
        self.assertIn('font-family:Oswald', html)
        self.assertNotIn("Iowan Old Style", html)

    def test_turns_without_timestamps(self):
        turns = json.loads((FIX / "turns.json").read_text())
        for t in turns:
            t["ts"] = ""
        r, out = self.build(turns=turns)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = out.read_text()
        self.assertNotIn('class="ts"', html)
        self.assertNotIn(" · </div>", html)



    # Refactoring UI checks
    def css(self):
        return (ROOT / "assets" / "style.css").read_text()

    def rule(self, selector):
        m = re.search(r"(?:^|[}\n])" + re.escape(selector) + r"\{([^}]*)\}", self.css())
        self.assertIsNotNone(m, selector)
        return m.group(1)

    def test_type_scale(self):
        sizes = {int(v) for v in re.findall(r"font-size:(\d+)px", self.css())}
        self.assertLessEqual(sizes, {12, 14, 16, 18, 20, 24, 30, 36, 48})

    def test_prose_measure(self):
        for sel in [".points", ".chunk-sum", ".text", ".grp h3", "h2.lead"]:
            m = re.search(r"max-width:(\d+)ch", self.rule(sel))
            self.assertIsNotNone(m, sel)
            self.assertLessEqual(int(m.group(1)), 75, sel)

    def test_fewer_borders(self):
        for sel in [".note", ".stat", ".hyp", "details.box"]:
            self.assertNotRegex(self.rule(sel), r"(^|;)border:1px", sel)
        self.assertNotIn("box-shadow", self.rule(".tabs"))

    def test_filter_buttons_are_secondary(self):
        self.assertNotIn("background:var(--fg)", self.rule(".btn"))

    def test_zero_stats_muted(self):
        def m(rep):
            sid = next(n["id"] for n in rep["notes"] if n["type"] == "signal")
            rep["notes"] = [n for n in rep["notes"] if n["id"] != sid]
            for part in rep["groups"]["parts"]:
                for g in part["groups"]:
                    g["notes"] = [x for x in g["notes"] if x != sid]
            f = rep["findings"]
            for h in f.get("hypotheses", []):
                h["evidence"] = [x for x in h.get("evidence", []) if x != sid]
            for q in f.get("next_questions", []):
                q["sources"] = [x for x in q.get("sources", []) if x != sid]
        r, out = self.build(m)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        html = out.read_text()
        self.assertIn('<div class="stat zero" data-type="signal">', html)
        self.assertIn('<div class="stat" data-type="job">', html)
        self.assertIn(".stat.zero", self.css())

    def test_mobile_tabs_wrap_and_bar_follows(self):
        css = self.css()
        m = re.search(r"@media \(max-width:500px\)\{(.*)\}\s*$", css, re.S)
        self.assertIsNotNone(m)
        self.assertIn(".tabs .wrap{flex-wrap:wrap", m.group(1))
        self.assertIn(".bar{top:var(--tabs-h", css)
        js = (ROOT / "scripts" / "report.js").read_text()
        self.assertIn("--tabs-h", js)

if __name__ == "__main__":
    unittest.main()
