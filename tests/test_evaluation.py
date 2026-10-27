"""Auswertung: Formatierung, Analyse, Tabellen, Verdikte und die Zahlen in den Hilfetexten der Presets."""

from types import SimpleNamespace


import arw_algorithm as A
import arw_constants as C
import arw_evaluation as ev
from arw_evaluation import Settings, analyse

HAND = C.PRESETS["Handbeispiel: zwei Wähler, zwei Alternativen"]


def test_formatierung():
    assert ev.num(1234.567, 1) == "1234,6" and ev.num(-0.5, 1) == "−0,5" and ev.pct(0.296) == "30 %" and ev.pct(None) == "–" and ev.pct(float("nan")) == "–"
    assert ev.seconds_text(0.0123) == "0,01 s" and ev.seconds_text(9.99) == "9,99 s" and ev.seconds_text(10.4) == "10 s" and ev.seconds_text(65.2) == "65 s"


def test_einstellungen_und_axiomtext():
    s = Settings()
    assert (s.n, s.m, s.domain) == (2, 3, "alle") and s.axioms() == ("pareto", "iia", "nd")
    assert Settings(iia=False).axioms() == ("pareto", "nd") and Settings(pareto=False, iia=False, nd=False).axioms() == ()
    assert ev.axiom_text(Settings()) == "Pareto + Unabhängigkeit irrelevanter Alternativen + Nichtdiktatur" and ev.axiom_text(Settings(pareto=False, iia=False, nd=False)) == "keine Axiome"


def test_analyse_unlösbar():
    a = analyse(Settings())
    assert (a.too_big, a.result.status, a.count, a.kinds, a.checked, a.follow) == (False, "unlösbar", 0, {}, None, None) and len(a.groups) == 11
    assert a.result.profiles == 36 and a.result.variables == 216 and a.complete


def test_analyse_lösbar_mit_aufzählung_und_gegenprobe():
    a = analyse(Settings(n=3, m=3, nd=False))
    assert a.result.status == "lösbar" and a.count == 3 and a.complete and a.kinds == {"Diktatur von Wähler 1": 1, "Diktatur von Wähler 2": 1, "Diktatur von Wähler 3": 1}
    assert a.checked == {"pareto": True, "iia": True, "nd": False} and sorted(a.follow, reverse=True)[0] == 1.0 and len(a.follow) == 3


def test_analyse_zu_groß():
    a = analyse(Settings(n=5, m=3))
    assert a.too_big and a.result is None and a.count == 0 and ev.summary_rows(a) == [] and ev.example_rows(a) == [] and ev.core_of(Settings(n=5, m=3)) is None
    assert not analyse(Settings(n=5, m=3, domain="einspitzig")).too_big


def test_kern_wird_nur_bei_unlösbarem_modell_geliefert():
    core = ev.core_of(Settings())
    assert len(core) == 9 and ev.core_of(Settings(nd=False)) is None
    rows = ev.core_rows(core)
    assert rows[0] == {"Bedingung": "Pareto: A vor C"} and {"Bedingung": "Nichtdiktatur: Wähler 2"} in rows and len(rows) == 9


# --- Tabellen ---------------------------------------------------------------------------------------------------------------------------------


def test_zusammenfassung_und_beispieltabelle():
    a = analyse(Settings(**HAND))
    row = ev.summary_rows(a)[0]
    assert (row["Profile"], row["Variablen"], row["Ergebnis"]) == (4, 8, "lösbar") and row["Rechenzeit"].endswith(" s")
    rows = ev.example_rows(a)
    assert len(rows) == 4 and set(rows[0]) == {"Wähler 1", "Wähler 2", "Ergebnis"} and rows[0] == {"Wähler 1": "A > B", "Wähler 2": "A > B", "Ergebnis": "A > B"}
    assert rows[3] == {"Wähler 1": "B > A", "Wähler 2": "B > A", "Ergebnis": "B > A"}


def test_beispieltabelle_wählt_gleichmäßig_höchstens_zwölf_profile():
    assert ev.sample_indices(4) == [0, 1, 2, 3] and ev.sample_indices(12) == list(range(12))
    idx = ev.sample_indices(36)
    assert len(idx) == 12 and idx[0] == 0 and idx[-1] == 35 and idx == sorted(set(idx))
    assert len(ev.example_rows(analyse(Settings(n=3, m=3, nd=False)))) == C.SAMPLE_PROFILES
    assert ev.sample_indices(13)[0] == 0 and ev.sample_indices(13)[-1] == 12


def test_arten_der_lösungen_und_zählung():
    a = analyse(Settings(n=3, m=3, pareto=False, nd=True))
    assert a.count == C.SOLUTION_CAP and not a.complete and ev.count_text(a) == "mindestens 500"
    kinds = ev.kind_rows(a)
    assert [k["Zahl"] for k in kinds] == sorted((k["Zahl"] for k in kinds), reverse=True) and sum(k["Zahl"] for k in kinds) == a.count
    assert ev.count_text(analyse(Settings(**HAND))) == "genau 2"


# --- Verdikte ---------------------------------------------------------------------------------------------------------------------------------


def test_verdikt_unlösbar_lösbar_und_diktaturen():
    kind, text = ev.verdict_state(analyse(Settings()))
    assert kind == "warning" and "Keine Wohlfahrtsfunktion erfüllt Pareto + Unabhängigkeit irrelevanter Alternativen + Nichtdiktatur (2 Wähler, 3 Alternativen, alle strikten Ordnungen)" in text and "aus 216 Variablen" in text
    kind, text = ev.verdict_state(analyse(Settings(n=3, m=3, nd=False)))
    assert kind == "success" and "genau 3 Wohlfahrtsfunktionen" in text and "Alle sind Diktaturen." in text and "Gefundenes Beispiel: Diktatur von Wähler" in text
    kind, text = ev.verdict_state(analyse(Settings(**HAND)))
    assert kind == "success" and "genau 2 Wohlfahrtsfunktionen" in text and "Alle sind Diktaturen" not in text
    kind, text = ev.verdict_state(analyse(Settings(n=3, m=3, pareto=False, nd=True)))
    assert "mindestens 500" in text and "Alle sind Diktaturen" not in text


def test_verdikt_zu_groß_und_zeitgrenze():
    kind, text = ev.verdict_state(analyse(Settings(n=5, m=3)))
    assert kind == "info" and "46656 Variablen" in text and "höchstens 20000" in text
    stub = SimpleNamespace(settings=Settings(), too_big=False, result=SimpleNamespace(status="unbekannt"))
    kind, text = ev.verdict_state(stub)
    assert kind == "warning" and "in 60 Sekunden keine Antwort" in text


def test_verdikt_diktaturen_nur_bei_vollständiger_aufzählung():
    base = dict(settings=Settings(), too_big=False, result=SimpleNamespace(status="lösbar", swf={p: p[0] for p in ((((0, 1, 2),),))}, seconds=0.0, variables=1), count=2)
    full = SimpleNamespace(kinds={"Diktatur von Wähler 1": 1, "Diktatur von Wähler 2": 1}, complete=True, **base)
    cut = SimpleNamespace(kinds={"Diktatur von Wähler 1": 1, "Diktatur von Wähler 2": 1}, complete=False, **base)
    assert "Alle sind Diktaturen." in ev.verdict_state(full)[1] and "Alle sind Diktaturen." not in ev.verdict_state(cut)[1] and "mindestens 2" in ev.verdict_state(cut)[1]


# --- Reihen mit ersetztem Löser ---------------------------------------------------------------------------------------------------------------


def test_reihe_lösbarkeit_ruft_jeden_fall_und_jede_variante_auf(monkeypatch):
    calls = []

    def fake_solve(n, m, domain, groups):
        calls.append((n, m, domain, tuple(sorted({g[0] for g in groups}))))
        return SimpleNamespace(status="unlösbar" if m >= 3 and len({g[0] for g in groups}) == 3 else "lösbar", seconds=0.5, variables=n * m)

    monkeypatch.setattr(A, "solve", fake_solve)
    rows = ev.series_cases()
    assert len(rows) == len(C.SERIES_CASES) * 4 == len(calls) and {(r["n"], r["m"]) for r in rows} == set(C.SERIES_CASES)
    assert [r["variante"] for r in rows[:4]] == ["alle drei", "ohne Pareto", "ohne Unabhängigkeit", "ohne Nichtdiktatur"]
    assert [c[3] for c in calls[:4]] == [("iia", "nd", "pareto"), ("iia", "nd"), ("nd", "pareto"), ("iia", "pareto")]
    assert all(c[2] == "alle" for c in calls)


def test_reihe_zählung_nutzt_pareto_und_unabhängigkeit(monkeypatch):
    seen = []

    def fake_enum(n, m, domain, groups, cap=None):
        seen.append(sorted({g[0] for g in groups}))
        return [{((0, 1), (0, 1)): (0, 1)} for _ in range(n)], True

    monkeypatch.setattr(A, "enumerate_solutions", fake_enum)
    monkeypatch.setattr(A, "classify", lambda s, n: "Diktatur von Wähler 1")
    rows = ev.series_counts()
    assert all(s == ["iia", "pareto"] for s in seen) and len(rows) == len(C.SERIES_COUNT_CASES)
    assert [(r["n"], r["m"], r["count"], r["dictatorships"], r["complete"]) for r in rows][:2] == [(2, 2, 2, 2, True), (3, 2, 3, 3, True)]


def test_reihe_bereich_markiert_zu_große_modelle(monkeypatch):
    monkeypatch.setattr(A, "solve", lambda n, m, domain, groups: SimpleNamespace(status="lösbar", seconds=0.1, profiles=7))
    rows = ev.series_domain()
    big = [r for r in rows if r["status"] == "zu groß"]
    assert {(r["n"], r["m"], r["domain"]) for r in big} == {(5, 3, "alle"), (3, 4, "alle")} and all(r["seconds"] == 0.0 for r in big)
    assert len(rows) == 10 and big[0]["profiles"] == 7776


def test_reihentabellen():
    cases = [{"n": 2, "m": 3, "variante": "alle drei", "status": "unlösbar", "seconds": 0.012, "variables": 216}]
    assert ev.cases_table(cases) == [{"Wähler": 2, "Alternativen": 3, "Axiome": "alle drei", "Ergebnis": "unlösbar", "Variablen": 216, "Rechenzeit": "0,01 s"}]
    counts = [{"n": 3, "m": 3, "count": 3, "complete": True, "dictatorships": 3}, {"n": 3, "m": 2, "count": 500, "complete": False, "dictatorships": 3}]
    assert ev.counts_table(counts)[0]["Lösungen mit Pareto und Unabhängigkeit"] == "3" and ev.counts_table(counts)[1]["Lösungen mit Pareto und Unabhängigkeit"] == "mindestens 500"
    dom = [{"n": 5, "m": 3, "domain": "alle", "status": "zu groß", "seconds": 0.0, "profiles": 7776}, {"n": 5, "m": 3, "domain": "einspitzig", "status": "lösbar", "seconds": 0.64, "profiles": 1024}]
    assert ev.domain_table(dom)[0]["Rechenzeit"] == "–" and ev.domain_table(dom)[1]["Rechenzeit"] == "0,64 s" and ev.domain_table(dom)[1]["Bereich"] == "Nur einspitzige Ordnungen"


# --- Verdikte der Reihen an handgesetzten Zeilen ------------------------------------------------------------------------------------------------


def _case(n, m, variante, status, seconds=0.1):
    return {"n": n, "m": m, "variante": variante, "status": status, "seconds": seconds, "variables": 1}


def test_verdikt_reihe_lösbarkeit():
    rows = [_case(2, 2, "alle drei", "lösbar"), _case(2, 3, "alle drei", "unlösbar", 0.3), _case(3, 3, "alle drei", "unlösbar", 0.7), _case(2, 3, "ohne Pareto", "lösbar", 2.5), _case(3, 3, "ohne Nichtdiktatur", "lösbar")]
    kind, text = ev.verdict_cases(rows)
    assert kind == "warning" and "in allen 2 Fällen mit mindestens drei Alternativen unlösbar (der Löser braucht dafür höchstens 0,70 s)" in text and "jede Lockerung ist lösbar (2 von 2 Fällen)" in text
    assert "Die längste Rechnung: ohne Pareto bei 2 Wählern und 3 Alternativen (2,50 s)" in text
    assert ev.verdict_cases([_case(2, 3, "alle drei", "lösbar"), _case(2, 3, "ohne Pareto", "lösbar")])[0] == "info"


def _count(n, m, count, dictatorships, complete=True):
    return {"n": n, "m": m, "count": count, "complete": complete, "dictatorships": dictatorships}


def test_verdikt_reihe_zahl_der_regeln():
    rows = [_count(2, 2, 4, 2), _count(3, 3, 3, 3), _count(2, 4, 2, 2)]
    kind, text = ev.verdict_counts(rows)
    assert kind == "success" and "genau so viele Lösungen wie Wähler" in text and "3 Wähler, 3 Alternativen: 3" in text and "2 Wähler: 4 (davon 2 Diktaturen)" in text
    assert ev.verdict_counts([_count(3, 3, 4, 3)])[0] == "info" and ev.verdict_counts([_count(3, 3, 3, 2)])[0] == "info" and ev.verdict_counts([_count(3, 3, 3, 3, complete=False)])[0] == "info"


def _dom(n, m, domain, status, profiles=64):
    return {"n": n, "m": m, "domain": domain, "status": status, "seconds": 0.1, "profiles": profiles}


def test_verdikt_reihe_bereich():
    rows = [_dom(3, 3, "alle", "unlösbar"), _dom(3, 3, "einspitzig", "lösbar", 64), _dom(5, 3, "alle", "zu groß", 7776), _dom(5, 3, "einspitzig", "lösbar", 1024)]
    kind, text = ev.verdict_domain(rows)
    assert kind == "success" and "in allen 1 gerechneten Fällen unlösbar" in text and "in 2 von 2 Fällen lösbar" in text and "bei 5 Wählern bis 1024 Profile" in text
    assert ev.verdict_domain([_dom(3, 3, "alle", "lösbar"), _dom(3, 3, "einspitzig", "lösbar")])[0] == "info" and ev.verdict_domain([_dom(3, 3, "alle", "unlösbar"), _dom(3, 3, "einspitzig", "unlösbar")])[0] == "info"


# --- Presets: jede Zahl im Hilfetext stimmt ---------------------------------------------------------------------------------------------------


def test_jedes_preset_hat_einen_hilfetext():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and all(C.PRESET_HELP.values())


def test_hilfetexte_der_presets_stimmen_mit_der_rechnung():
    a = analyse(Settings(**C.PRESETS["Arrow: zwei Wähler, drei Alternativen"]))
    assert a.result.status == "unlösbar" and (a.result.profiles, a.result.variables) == (36, 216) and len(ev.core_of(a.settings)) == 9 and "9 von 11" in C.PRESET_HELP["Arrow: zwei Wähler, drei Alternativen"]
    b = analyse(Settings(**C.PRESETS["Drei Wähler, drei Alternativen"]))
    assert b.result.status == "unlösbar" and (b.result.profiles, b.result.variables) == (216, 1296) and len(ev.core_of(b.settings)) == 10
    assert "216 Profile, 1.296 Variablen" in C.PRESET_HELP["Drei Wähler, drei Alternativen"] and "10 von 12" in C.PRESET_HELP["Drei Wähler, drei Alternativen"]
    c = analyse(Settings(**C.PRESETS["Ohne Nichtdiktatur"]))
    assert c.count == 3 and c.complete and all(k.startswith("Diktatur") for k in c.kinds)
    for name in ("Ohne Unabhängigkeit", "Ohne Pareto", "Einspitzige Ordnungen"):
        d = analyse(Settings(**C.PRESETS[name]))
        assert d.result.status == "lösbar" and d.count == 500 and not d.complete and "500" in C.PRESET_HELP[name]
    two = analyse(Settings(**C.PRESETS["Nur zwei Alternativen"]))
    assert two.count == 61 and two.complete and "genau 61" in C.PRESET_HELP["Nur zwei Alternativen"] and "64 mit Pareto" in C.PRESET_HELP["Nur zwei Alternativen"]
    hand = analyse(Settings(**HAND))
    assert hand.count == 2 and hand.complete and "genau zwei" in C.PRESET_HELP["Handbeispiel: zwei Wähler, zwei Alternativen"]


def test_borda_und_feste_rangfolge_kommen_unter_den_lösungen_vor():
    assert "feste Rangfolge" in analyse(Settings(n=3, m=3, pareto=False)).kinds                                       # Hilfetext „Ohne Pareto“
    assert "Borda" in C.PRESET_HELP["Ohne Unabhängigkeit"] and "feste Rangfolgen" in C.PRESET_HELP["Ohne Pareto"]
