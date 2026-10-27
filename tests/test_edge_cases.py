"""Randfälle: alle Axiomauswahlen, Bereiche und Größen; Invarianten jeder Analyse; Adresszeile und Kern auf Klick."""

import itertools
import os

import pytest
from streamlit.testing.v1 import AppTest

import arw_algorithm as A
import arw_constants as C
import arw_evaluation as ev
import arw_scenario as S

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
SUBSETS = [dict(pareto=p, iia=i, nd=d) for p, i, d in itertools.product((True, False), repeat=3)]
SIZES = [(n, m, domain) for n in (2, 3) for m in (2, 3) for domain in ("alle", "einspitzig")] + [(4, 2, "alle"), (5, 2, "alle")]      # größere Fälle: Orakel, Reihen und Claims


@pytest.mark.parametrize("n,m,domain", SIZES)
def test_invarianten_für_alle_axiomauswahlen(n, m, domain):
    if not S.size_ok(n, m, domain):
        pytest.skip("zu groß")
    for flags in SUBSETS:
        a = ev.analyse(ev.Settings(n=n, m=m, domain=domain, **flags))
        assert not a.too_big and a.result.status in ("lösbar", "unlösbar")
        assert len(a.groups) == len(A.groups_for(n, m, a.settings.axioms()))
        if a.result.status == "lösbar":
            assert a.result.swf and a.count >= 1 and sum(a.kinds.values()) == a.count and len(ev.example_rows(a)) == min(len(a.result.swf), C.SAMPLE_PROFILES)
            checked = A.check_axioms(a.result.swf, n, m)
            assert all(checked[ax] for ax in a.settings.axioms()) and a.checked == checked
            assert len(a.follow) == n and all(0 <= f <= 1 for f in a.follow)
        else:
            assert a.count == 0 and a.kinds == {} and a.follow is None
        assert ev.verdict_state(a)[1]


def test_arrow_gilt_genau_für_alle_ordnungen_ab_drei_alternativen():
    for n, m in ((2, 3), (3, 3), (2, 4)):
        assert ev.analyse(ev.Settings(n=n, m=m)).result.status == "unlösbar"
        assert ev.analyse(ev.Settings(n=n, m=m, domain="einspitzig")).result.status == "lösbar"
    for n in (2, 3, 4):
        assert ev.analyse(ev.Settings(n=n, m=2)).result.status == "lösbar"


def test_ohne_axiome_gibt_es_viele_funktionen():
    a = ev.analyse(ev.Settings(n=2, m=3, pareto=False, iia=False, nd=False))
    assert a.result.status == "lösbar" and a.count == C.SOLUTION_CAP and not a.complete


def test_eine_alternative_ist_nicht_wählbar_aber_zwei_wähler_zwei_alternativen_sind_das_minimum():
    assert C.M_MIN == 2 and C.N_MIN == 2
    a = ev.analyse(ev.Settings(n=C.N_MIN, m=C.M_MIN))
    assert a.result.status == "lösbar" and a.count == 2


# --- App: Adresszeile und Kern auf Klick -------------------------------------------------------------------------------------------------------


def _run(**params):
    at = AppTest.from_file(APP, default_timeout=180)
    for key, value in params.items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_setzt_schalter_regler_und_bereich():
    at = _run(n="3", m="3", pareto="True", iia="False", nd="true", domain="einspitzig")
    assert at.sidebar.slider(key="n_slider").value == 3 and at.sidebar.slider(key="m_slider").value == 3
    assert at.sidebar.toggle(key="iia_toggle").value is False and at.sidebar.toggle(key="pareto_toggle").value is True
    assert at.sidebar.selectbox(key="domain_select").value == "einspitzig"
    assert [m.label for m in at.metric] == ["Ergebnis des Lösers", "Variablen", "Lösungen"] and at.metric[0].value == "lösbar"


def test_permalink_werte_werden_begrenzt_und_schlechte_ignoriert():
    at = _run(n="99", m="x", pareto="vielleicht", domain="Mitte")
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.slider(key="m_slider").value == C.DEFAULT_M
    assert at.sidebar.toggle(key="pareto_toggle").value is True and at.sidebar.selectbox(key="domain_select").value == "alle"
    assert any("46656 Variablen" in i.value for i in at.info) or at.info                                          # n = 5, m = 3: zu groß


def test_standardlauf_zeigt_unlösbar_und_das_urteil():
    at = _run()
    assert at.metric[0].value == "unlösbar" and at.metric[1].value == "216" and at.metric[2].value == "keine"
    assert any("Keine Wohlfahrtsfunktion erfüllt" in w.value for w in at.warning)


def test_kern_auf_klick():
    at = _run()
    assert not any("Kern" in t.value for t in at.table) and at.button(key="core_button")
    at.button(key="core_button").click().run(timeout=180)
    assert not at.exception, [str(e) for e in at.exception]
    rows = [t for t in at.table if "Bedingung" in list(t.value.columns)]
    assert len(rows) == 1 and len(rows[0].value) == 9 and any("9 von 11 Bedingungsgruppen genügen" in c.value for c in at.caption)


def test_lösbarer_fall_zeigt_beispiel_gitter_und_arten():
    at = _run(n="2", m="3", nd="False")
    assert at.metric[0].value == "lösbar" and at.metric[2].value == "2"
    labels = [t.value.columns.tolist() for t in at.table]
    assert ["Wähler 1", "Wähler 2", "Ergebnis"] in labels and ["Art der Lösung", "Zahl"] in labels
    assert any("Gegenprobe nach den Definitionen" in c.value for c in at.caption)


def test_regler_und_schalter_ändern_hält_die_app_am_laufen():
    at = _run()
    for key, value in (("n_slider", 4), ("n_slider", 5), ("m_slider", 4), ("m_slider", 2), ("n_slider", 2)):
        at.sidebar.slider(key=key).set_value(value).run()
        assert not at.exception
    for key in ("pareto_toggle", "iia_toggle", "nd_toggle"):
        at.sidebar.toggle(key=key).set_value(False).run()
        assert not at.exception
    at.sidebar.selectbox(key="domain_select").set_value("einspitzig").run()
    assert not at.exception


def test_die_reihen_laufen_auf_klick():
    at = _run()
    for key in ("cases_button", "counts_button", "domain_button"):
        at.button(key=key).click().run(timeout=180)
        assert not at.exception, [str(e) for e in at.exception]
    assert len(at.table) == 4                                                       # Größe des Modells (Expander) und drei Reihentabellen
