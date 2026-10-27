"""Abbildungen: Zahl und Art der Spuren, gesperrte Achsen, Werte aus der Analyse und den Reihen."""

import pytest

import arw_constants as C
import arw_evaluation as ev
import arw_visualization as V

HAND = C.PRESETS["Handbeispiel: zwei Wähler, zwei Alternativen"]


def _locked(fig):
    return fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_kurzschreibweise():
    assert V.short((2, 0, 1)) == "CAB"


def test_folgeabbildung_einer_diktatur():
    a = ev.analyse(ev.Settings(n=3, m=3, nd=False))
    fig = V.build_follow(a)
    assert _locked(fig) and list(fig.data[0].x) == ["Wähler 1", "Wähler 2", "Wähler 3"] and max(fig.data[0].y) == pytest.approx(100.0)
    assert [round(v) for v in fig.data[0].y if v < 99] != [] and len(fig.data[0].marker.color) == 3


def test_gitter_bei_zwei_wählern():
    a = ev.analyse(ev.Settings(**HAND))
    fig = V.build_grid(a)
    heat = fig.data[0]
    assert _locked(fig) and list(heat.x) == ["AB", "BA"] and list(heat.y) == ["AB", "BA"]
    assert [list(r) for r in heat.text] == [[t for t in row] for row in [["AB", a_cell(a, 0, 1)], [a_cell(a, 1, 0), "BA"]]]


def a_cell(a, i, j):
    orders = [(0, 1), (1, 0)]
    return V.short(a.result.swf[(orders[i], orders[j])])


def test_gitter_nur_bei_zwei_wählern_und_lösbarem_modell():
    assert V.build_grid(ev.analyse(ev.Settings(n=3, m=3, nd=False))) is None
    assert V.build_grid(ev.analyse(ev.Settings())) is None                       # unlösbar: keine Funktion
    big = V.build_grid(ev.analyse(ev.Settings(n=2, m=3, nd=False)))
    assert len(big.data[0].x) == 6 and len(big.data[0].text) == 6 and big.layout.height == 120 + 52 * 6


def _cases():
    rows = []
    for n, m in C.SERIES_CASES:
        for label in ("alle drei", "ohne Pareto", "ohne Unabhängigkeit", "ohne Nichtdiktatur"):
            rows.append({"n": n, "m": m, "variante": label, "status": "unlösbar" if (m >= 3 and label == "alle drei") else "lösbar", "seconds": 0.1, "variables": 1})
    return rows


def test_lösbarkeitskarte():
    fig = V.build_cases(_cases())
    heat = fig.data[0]
    assert _locked(fig) and len(heat.y) == len(C.SERIES_CASES) and list(heat.x) == ["alle drei", "ohne Pareto", "ohne Unabhängigkeit", "ohne Nichtdiktatur"]
    assert list(heat.y)[2] == "2 Wähler, 3 Alternativen" and heat.z[2][0] == 0 and heat.z[2][1] == 1 and heat.z[0][0] == 1                 # unlösbar = 0 (rot), lösbar = 1 (grün)


def test_zählabbildung_logarithmisch():
    rows = [{"n": 2, "m": 3, "count": 2, "complete": True, "dictatorships": 2}, {"n": 3, "m": 2, "count": 64, "complete": True, "dictatorships": 3}]
    fig = V.build_counts(rows)
    assert _locked(fig) and fig.layout.yaxis.type == "log" and [t.name for t in fig.data] == ["Lösungen", "davon Diktaturen"]
    assert list(fig.data[0].x) == ["2 W., 3 A.", "3 W., 2 A."] and list(fig.data[0].y) == [2, 64] and list(fig.data[1].y) == [2, 3]


def test_bereichskarte_mit_zu_großen_modellen():
    rows = [{"n": 3, "m": 3, "domain": "alle", "status": "unlösbar", "seconds": 0.1, "profiles": 216}, {"n": 3, "m": 3, "domain": "einspitzig", "status": "lösbar", "seconds": 0.1, "profiles": 64},
            {"n": 5, "m": 3, "domain": "alle", "status": "zu groß", "seconds": 0.0, "profiles": 7776}, {"n": 5, "m": 3, "domain": "einspitzig", "status": "lösbar", "seconds": 0.5, "profiles": 1024}]
    fig = V.build_domain(rows)
    heat = fig.data[0]
    assert _locked(fig) and list(heat.x) == ["Alle strikten Ordnungen", "Nur einspitzige Ordnungen"] and list(heat.z[0]) == [0, 1] and list(heat.z[1]) == [0.5, 1]
