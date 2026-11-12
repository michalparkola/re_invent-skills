#!/usr/bin/env python3
"""Tests for prepare_turns.py and build_report.py. Run: python3 tests/test_scripts.py"""
import copy, json, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
PREP = ROOT / "scripts" / "prepare_turns.py"
BUILD = ROOT / "scripts" / "build_report.py"
TEMPLATE = ROOT / "assets" / "report.html"
SLOT = '<script type="application/json" id="report-data">null</script>'
HAS_NODE = shutil.which("node") is not None


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)


def page_script(page):
    """The renderer script of a page: the last <script> without a type."""
    return re.findall(r"<script>(.*?)</script>", page, re.S)[-1]


def page_data(page):
    m = re.search(r'<script type="application/json" id="report-data">(.*?)</script>', page, re.S)
    return json.loads(m.group(1))


def render_js(page, data=None):
    """Run the page's renderer in node. Returns {title, lang, store, html}."""
    data = page_data(page) if data is None else data
    code = ("const src=require('fs').readFileSync(0,'utf8');const {js,data}=JSON.parse(src);"
            "const m={};new Function('module',js)(m);"
            "process.stdout.write(JSON.stringify(m.exports.render(data)));")
    r = subprocess.run(["node", "-e", code], input=json.dumps({"js": page_script(page), "data": data}),
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


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
        self.assertIn("input-formats.md", r.stdout + r.stderr)

    def rows(self, turns):
        return [(t["sp"], t["ts"], t["text"]) for t in turns]

    def test_srt_with_name_prefix_or_brackets(self):
        srt = ("1\n00:00:01,400 --> 00:00:04,000\nAnna: Opowiedz o ostatnim\nzamknięciu miesiąca.\n\n"
               "2\n00:00:05,000 --> 00:00:07,000\n[Jan] W marcu.\n\n"
               "3\n00:00:07,500 --> 00:00:09,000\nTrwało tydzień.\n\n"
               "4\n00:01:05,000 --> 00:01:07,000\n[Anna]: Ile dni?\n")
        self.assertEqual(self.rows(self.prep("t.srt", srt)), [
            ("A", "00:00:01", "Opowiedz o ostatnim zamknięciu miesiąca."),
            ("J", "00:00:05", "W marcu. Trwało tydzień."),
            ("A", "00:01:05", "Ile dni?")])

    def test_vtt_voice_tags(self):
        vtt = ("WEBVTT\n\nNOTE exported by a meeting tool\n\n"
               "3f2a-1\n00:03.000 --> 00:05.200\n<v Anna Nowak>Opowiedz o <c>marcu</c>.</v>\n\n"
               "3f2a-2\n00:06.000 --> 00:08.000 align:start\n<v.loud Jan Kowalski>Trzy noce.</v>\n\n"
               "3f2a-3\n01:00:01.000 --> 01:00:03.000\n<v Jan Kowalski>W Excelu.</v>\n")
        self.assertEqual(self.rows(self.prep("t.vtt", vtt)), [
            ("A", "00:00:03", "Opowiedz o marcu."),
            ("J", "00:00:06", "Trzy noce. W Excelu.")])

    def test_vtt_name_prefix(self):
        vtt = ("WEBVTT\n\n1\n00:00:02.100 --> 00:00:04.000\nAnna Nowak: Jak to wyglądało?\n\n"
               "2\n00:00:05.000 --> 00:00:06.000\nJan Kowalski: Ręcznie.\n")
        self.assertEqual(self.rows(self.prep("t.vtt", vtt)), [
            ("A", "00:00:02", "Jak to wyglądało?"), ("J", "00:00:05", "Ręcznie.")])

    def test_name_and_time_header_blocks(self):
        txt = ("Anna Nowak  0:03\nOpowiedz o marcu.\n\n"
               "Jan Kowalski - 00:09\nTrzy noce.\nW Excelu.\n\n"
               "00:01:05 Anna Nowak\nIle dni?\n")
        self.assertEqual(self.rows(self.prep("t.txt", txt)), [
            ("A", "00:00:03", "Opowiedz o marcu."),
            ("J", "00:00:09", "Trzy noce. W Excelu."),
            ("A", "00:01:05", "Ile dni?")])

    def test_subtitles_without_speakers_fail_with_advice(self):
        d = Path(tempfile.mkdtemp()); p = d / "t.srt"
        p.write_text("1\n00:00:01,000 --> 00:00:03,000\nOpowiedz o marcu.\n\n2\n00:00:04,000 --> 00:00:05,000\nTrzy noce.\n")
        r = run(PREP, p, d / "o.json")
        self.assertNotEqual(r.returncode, 0)
        msg = r.stdout + r.stderr
        self.assertIn("speaker", msg.lower())
        self.assertIn("input-formats.md", msg)


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

    def rendered(self, out):
        if not HAS_NODE:
            self.skipTest("node not installed")
        return render_js(out.read_text())

    def test_valid_report_builds_one_tabbed_page(self):
        r, out = self.build()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        res = self.rendered(out)
        self.assertEqual(res["lang"], "pl")
        self.assertEqual(res["title"], "Jan, wywiad 1")
        html = res["html"]
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
        self.assertIn("Missed opportunity", self.rendered(out)["html"])

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
        html = self.rendered(out)["html"]
        self.assertNotIn('class="ts"', html)
        self.assertNotIn(" · </div>", html)



    # Refactoring UI checks
    def css(self):
        return re.search(r"<style>(.*?)</style>", TEMPLATE.read_text(), re.S).group(1)

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
        html = self.rendered(out)["html"]
        self.assertIn('<div class="stat zero" data-type="signal">', html)
        self.assertIn('<div class="stat" data-type="job">', html)
        self.assertIn(".stat.zero", self.css())

    def test_mobile_tabs_wrap_and_bar_follows(self):
        css = self.css()
        m = re.search(r"@media \(max-width:500px\)\{(.*)\}\s*$", css, re.S)
        self.assertIsNotNone(m)
        self.assertIn(".tabs .wrap{flex-wrap:wrap", m.group(1))
        self.assertIn(".bar{top:var(--tabs-h", css)
        js = page_script(TEMPLATE.read_text())
        self.assertIn("--tabs-h", js)

class Template(unittest.TestCase):
    """One template renders the page, with or without the build script."""

    def test_single_source(self):
        page = TEMPLATE.read_text()
        self.assertEqual(page.count(SLOT), 1)
        self.assertFalse((ROOT / "assets" / "style.css").exists())
        self.assertFalse((ROOT / "scripts" / "report.js").exists())

    def test_build_puts_data_in_template(self):
        rep = json.loads((FIX / "report.json").read_text())
        rep["summary"]["headline"] = "Jan </script><b>płaci</b>"
        d = Path(tempfile.mkdtemp())
        (d / "r.json").write_text(json.dumps(rep, ensure_ascii=False))
        r = run(BUILD, "--turns", FIX / "turns.json", "--report", d / "r.json", "--out", d / "o.html")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        page = (d / "o.html").read_text()
        self.assertNotIn("</script><b>", page)
        self.assertEqual(page_data(page)["report"]["summary"]["headline"], "Jan </script><b>płaci</b>")
        self.assertEqual(page.replace(re.search(r'id="report-data">(.*?)</script>', page, re.S).group(1), "null"),
                         TEMPLATE.read_text())
        if HAS_NODE:
            self.assertIn("Jan &lt;/script&gt;&lt;b&gt;płaci", render_js(page)["html"])

    @unittest.skipUnless(HAS_NODE, "node not installed")
    def test_renderer_flags_bad_quote_without_script(self):
        data = {"turns": json.loads((FIX / "turns.json").read_text()),
                "report": json.loads((FIX / "report.json").read_text())}
        data["report"]["notes"][1]["quote"] = "siedziałem trzy noce"
        html = render_js(TEMPLATE.read_text(), data)["html"]
        self.assertIn('class="problems"', html)
        self.assertIn("siedziałem trzy noce", html)
        self.assertEqual(html.count('<aside class="note"'), 6)

    @unittest.skipUnless(HAS_NODE, "node not installed")
    def test_empty_template_explains_itself(self):
        html = render_js(TEMPLATE.read_text(), None)["html"]
        self.assertIn("report-data", html)


if __name__ == "__main__":
    unittest.main()
