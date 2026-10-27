"""Befunde der festen Reihen: jede Aussage der README und der Verdikte steht hier als Prüfung. Alle Fälle sind exakt gelöst (kein Zufall); geprüft werden Ergebnisse und Zahlen von Lösungen, nie die Rechenzeiten, die vom Rechner abhängen."""

import pytest

import arw_constants as C
import arw_evaluation as ev


@pytest.fixture(scope="module")
def cases():
    return ev.series_cases()


@pytest.fixture(scope="module")
def counts():
    return ev.series_counts()


@pytest.fixture(scope="module")
def domains():
    return ev.series_domain()


def pick(rows, **kw):
    found = [r for r in rows if all(r[k] == v for k, v in kw.items())]
    assert len(found) == 1, kw
    return found[0]


# --- Reihe 1: Lösbarkeit je Größe und Axiomauswahl -----------------------------------------------------------------------------------------------


def test_reihe_1_aufbau(cases):
    assert len(cases) == len(C.SERIES_CASES) * 4 == 24 and ev.cases_table(cases)[0]["Wähler"] == 2


def test_alle_drei_axiome_sind_ab_drei_alternativen_unlösbar(cases):
    for n, m in C.SERIES_CASES:
        r = pick(cases, n=n, m=m, variante="alle drei")
        assert r["status"] == ("unlösbar" if m >= 3 else "lösbar"), (n, m)
    assert sum(1 for r in cases if r["variante"] == "alle drei" and r["status"] == "unlösbar") == 4                     # (2,3), (3,3), (4,3), (2,4)


def test_jede_lockerung_ist_lösbar(cases):
    assert all(r["status"] == "lösbar" for r in cases if r["variante"] != "alle drei")


def test_größen_der_modelle(cases):
    sizes = {(r["n"], r["m"]): r["variables"] for r in cases}
    assert sizes == {(2, 2): 8, (3, 2): 16, (2, 3): 216, (3, 3): 1296, (4, 3): 7776, (2, 4): 13824}


def test_verdikt_reihe_1(cases):
    kind, text = ev.verdict_cases(cases)
    assert kind == "warning" and "in allen 4 Fällen mit mindestens drei Alternativen unlösbar" in text and "jede Lockerung ist lösbar (18 von 18 Fällen)" in text


# --- Reihe 2: Zahl der Regeln ---------------------------------------------------------------------------------------------------------------------


def test_reihe_2_aufbau(counts):
    assert [(r["n"], r["m"]) for r in counts] == list(C.SERIES_COUNT_CASES) and all(r["complete"] for r in counts)


def test_ab_drei_alternativen_bleiben_genau_die_diktaturen(counts):
    for r in counts:
        if r["m"] >= 3:
            assert r["count"] == r["n"] == r["dictatorships"]                                                           # README: 2, 3, 4, 2


def test_bei_zwei_alternativen_gibt_es_mehr_regeln(counts):
    assert pick(counts, n=2, m=2)["count"] == 4 and pick(counts, n=2, m=2)["dictatorships"] == 2                          # README: 4 von 2 Diktaturen
    assert pick(counts, n=3, m=2)["count"] == 64 and pick(counts, n=3, m=2)["dictatorships"] == 3


def test_verdikt_reihe_2(counts):
    kind, text = ev.verdict_counts(counts)
    assert kind == "success" and "genau so viele Lösungen wie Wähler" in text and "2 Wähler: 4 (davon 2 Diktaturen), 3 Wähler: 64 (davon 3 Diktaturen)" in text


# --- Reihe 3: engerer Bereich ---------------------------------------------------------------------------------------------------------------------


def test_reihe_3_aufbau(domains):
    assert len(domains) == 10 and ev.domain_table(domains)[0]["Bereich"] == "Alle strikten Ordnungen"


def test_alle_ordnungen_unlösbar_einspitzig_lösbar(domains):
    for n, m in ((3, 3), (4, 3), (2, 4)):
        assert pick(domains, n=n, m=m, domain="alle")["status"] == "unlösbar" and pick(domains, n=n, m=m, domain="einspitzig")["status"] == "lösbar"
    assert pick(domains, n=5, m=3, domain="alle")["status"] == "zu groß" and pick(domains, n=5, m=3, domain="einspitzig")["status"] == "lösbar"
    assert pick(domains, n=3, m=4, domain="alle")["status"] == "zu groß" and pick(domains, n=3, m=4, domain="einspitzig")["status"] == "lösbar"


def test_profilzahlen_im_einspitzigen_bereich(domains):
    assert pick(domains, n=3, m=3, domain="einspitzig")["profiles"] == 64 and pick(domains, n=5, m=3, domain="einspitzig")["profiles"] == 1024 and pick(domains, n=3, m=4, domain="einspitzig")["profiles"] == 512
    assert pick(domains, n=5, m=3, domain="alle")["profiles"] == 7776


def test_verdikt_reihe_3(domains):
    kind, text = ev.verdict_domain(domains)
    assert kind == "success" and "in allen 3 gerechneten Fällen unlösbar" in text and "in 5 von 5 Fällen lösbar" in text and "bei 5 Wählern bis 1024 Profile" in text
