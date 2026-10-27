"""Orakel: unabhängige Gegenproben. (1) Bei zwei Alternativen werden ALLE Wohlfahrtsfunktionen aufgezählt und mit dem Prüfer der Axiome gefiltert; die Zahl stimmt mit der Aufzählung des Lösers überein. (2) Ein zweites Modell (scipy, HiGHS, eigener Aufbau
ohne den Code des Kerns) ist genau dann lösbar, wenn CP-SAT lösbar meldet. (3) Zeugen von Hand: Diktatur, feste Rangfolge, Bordafunktion mit Gleichstandsbrecher und die Mehrheitsrelation auf einspitzigen Ordnungen erfüllen genau die erwarteten Axiome.
(4) Der Satz selbst: mit Pareto und Unabhängigkeit bleiben ab drei Alternativen genau n Lösungen, alle Diktaturen."""

import itertools

import numpy as np
import pytest
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

import arw_algorithm as A
import arw_scenario as S

ALL = ("pareto", "iia", "nd")
SUBSETS = [tuple(a for a in ALL if a in sub) for k in range(4) for sub in itertools.combinations(ALL, k)]


# --- (1) Alle Funktionen aufzählen ------------------------------------------------------------------------------------------------------------


def brute_force_count(n, m, axioms):
    profs = S.profiles(n, m, "alle")
    outs = S.linear_orders(m)
    count = 0
    for assignment in itertools.product(outs, repeat=len(profs)):
        swf = dict(zip(profs, assignment))
        checked = A.check_axioms(swf, n, m)
        if all(checked[a] for a in axioms):
            count += 1
    return count


@pytest.mark.parametrize("n,m", [(2, 2), (3, 2)])
def test_aufzählung_aller_funktionen_gegen_den_löser(n, m):
    for axioms in SUBSETS:
        brute = brute_force_count(n, m, axioms)
        sols, complete = A.enumerate_solutions(n, m, "alle", A.groups_for(n, m, axioms), cap=10**6)
        assert complete and len(sols) == brute, axioms
        assert A.solve(n, m, "alle", A.groups_for(n, m, axioms)).status == ("lösbar" if brute else "unlösbar")


def test_zahlen_der_handbeispiele_von_hand():
    # n = 2, m = 2: vier Profile, Pareto legt zwei fest, vier Möglichkeiten bei Uneinigkeit, zwei Diktaturen → 2 mit allen Axiomen, 4 mit Pareto und IIA
    assert brute_force_count(2, 2, ALL) == 2 and brute_force_count(2, 2, ("pareto", "iia")) == 4
    # n = 3, m = 2: sechs Profile mit Uneinigkeit frei (2^6 = 64), drei Diktaturen → 61 und 64
    assert brute_force_count(3, 2, ALL) == 61 and brute_force_count(3, 2, ("pareto", "iia")) == 64


# --- (2) Zweites Modell mit HiGHS --------------------------------------------------------------------------------------------------------------


def highs_feasible(n, m, domain, axioms):
    """Eigener Aufbau desselben Problems als gemischt-ganzzahliges Programm: Variablen je (Profil, Ausgabeordnung), Gleichungen und Schranken."""
    orders = S.domain_orders(m, domain)
    outs = list(itertools.permutations(range(m)))
    profs = list(itertools.product(orders, repeat=n))
    pi = {p: i for i, p in enumerate(profs)}
    oi = {o: j for j, o in enumerate(outs)}
    var = lambda p, o: pi[p] * len(outs) + oi[o]  # noqa: E731
    nv = len(profs) * len(outs)
    rows, lo, hi = [], [], []
    mat = lil_matrix((len(profs) + 1 + len(profs) * 3 * m * m + n, nv))
    r = 0

    def add(coeffs, low, high):
        nonlocal r
        for v, c in coeffs.items():
            mat[r, v] += c
        rows.append(r)
        lo.append(low)
        hi.append(high)
        r += 1

    for p in profs:
        add({var(p, o): 1 for o in outs}, 1, 1)
    lower = np.zeros(nv)
    upper = np.ones(nv)
    before = lambda o, a, b: o.index(a) < o.index(b)  # noqa: E731
    for a, b in itertools.permutations(range(m), 2):
        if "pareto" in axioms:
            for p in profs:
                if all(before(v, a, b) for v in p):
                    for o in outs:
                        if not before(o, a, b):
                            upper[var(p, o)] = 0
    if "iia" in axioms:
        for a, b in itertools.combinations(range(m), 2):
            first = {}
            for p in profs:
                key = tuple(before(v, a, b) for v in p)
                if key in first:
                    q = first[key]
                    coeffs = {}
                    for o in outs:
                        if before(o, a, b):
                            coeffs[var(q, o)] = coeffs.get(var(q, o), 0) + 1
                            coeffs[var(p, o)] = coeffs.get(var(p, o), 0) - 1
                    add(coeffs, 0, 0)
                else:
                    first[key] = p
    if "nd" in axioms:
        for i in range(n):
            add({var(p, p[i]): 1 for p in profs}, 0, len(profs) - 1)
    result = milp(c=np.zeros(nv), constraints=LinearConstraint(mat[:r].tocsr(), np.array(lo), np.array(hi)), integrality=np.ones(nv), bounds=Bounds(lower, upper))
    return result.status == 0


@pytest.mark.parametrize("n,m,domain", [(2, 3, "alle"), (3, 3, "alle"), (2, 3, "einspitzig"), (3, 3, "einspitzig"), (4, 3, "einspitzig")])
def test_zweites_modell_stimmt_mit_dem_löser_für_alle_axiomauswahlen(n, m, domain):
    for axioms in SUBSETS:
        expected = A.solve(n, m, domain, A.groups_for(n, m, axioms)).status == "lösbar"
        assert highs_feasible(n, m, domain, axioms) == expected, (n, m, domain, axioms)


def test_zweites_modell_beweist_arrow_für_vier_alternativen_und_zwei_wähler():
    assert not highs_feasible(2, 4, "alle", ALL)
    assert highs_feasible(2, 4, "alle", ("pareto", "iia"))                                          # ohne Nichtdiktatur lösbar


# --- (3) Zeugen von Hand ------------------------------------------------------------------------------------------------------------------------


def majority_order(profile, m):
    """Mehrheitsrelation (nur bei ungerader Wählerzahl eindeutig): Alternativen nach der Zahl der Siege im paarweisen Vergleich, die meisten zuerst."""
    n = len(profile)
    wins = {a: sum(1 for b in range(m) if b != a and sum(S.prefers(v, a, b) for v in profile) * 2 > n) for a in range(m)}
    return tuple(sorted(range(m), key=lambda a: -wins[a]))


def test_mehrheit_auf_einspitzigen_ordnungen_erfüllt_alle_axiome():
    for n in (3, 5):
        swf = {p: majority_order(p, 3) for p in S.profiles(n, 3, "einspitzig")}
        for p, o in swf.items():                                                              # das Ergebnis ist wirklich die paarweise Mehrheit (transitiv)
            for a, b in itertools.combinations(range(3), 2):
                assert S.prefers(o, a, b) == (sum(S.prefers(v, a, b) for v in p) * 2 > n)
        assert A.check_axioms(swf, n, 3) == {"pareto": True, "iia": True, "nd": True}


def test_mehrheit_auf_allen_ordnungen_ist_nicht_immer_transitiv():
    # Condorcet-Zyklus: A > B > C, B > C > A, C > A > B — die paarweise Mehrheit ergibt keine Ordnung (jede Alternative gewinnt einmal und verliert einmal)
    cyc = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
    wins = [sum(1 for b in range(3) if b != a and sum(S.prefers(v, a, b) for v in cyc) * 2 > 3) for a in range(3)]
    assert wins == [1, 1, 1]


def test_zeugen_erfüllen_genau_die_erwarteten_axiome():
    n, m = 3, 3
    cases = {
        "Diktatur": ({p: p[0] for p in S.profiles(n, m, "alle")}, {"pareto": True, "iia": True, "nd": False}),
        "feste Rangfolge": ({p: (0, 1, 2) for p in S.profiles(n, m, "alle")}, {"pareto": False, "iia": True, "nd": True}),
    }
    borda = {}
    for p in S.profiles(n, m, "alle"):
        score = {a: sum(v.index(a) for v in p) for a in range(m)}
        borda[p] = tuple(sorted(range(m), key=lambda a: (score[a], a)))
    cases["Borda"] = (borda, {"pareto": True, "iia": False, "nd": True})
    for name, (swf, expected) in cases.items():
        assert A.check_axioms(swf, n, m) == expected, name


# --- (4) Der Satz -----------------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("n,m", [(2, 3), (3, 3), (4, 3), (2, 4)])
def test_mit_pareto_und_unabhängigkeit_bleiben_genau_die_diktaturen(n, m):
    sols, complete = A.enumerate_solutions(n, m, "alle", A.groups_for(n, m, ("pareto", "iia")))
    assert complete and len(sols) == n
    assert sorted(A.classify(s, n) for s in sols) == [f"Diktatur von Wähler {i + 1}" for i in range(n)]
    for s in sols:
        assert A.check_axioms(s, n, m) == {"pareto": True, "iia": True, "nd": False}


def test_jede_gefundene_funktion_erfüllt_die_gewählten_axiome_nach_der_definition():
    for axioms in SUBSETS:
        sols, _ = A.enumerate_solutions(3, 3, "alle", A.groups_for(3, 3, axioms), cap=40)
        for s in sols:
            checked = A.check_axioms(s, 3, 3)
            assert all(checked[a] for a in axioms)
        assert len({tuple(sorted(s.items())) for s in sols}) == len(sols)                                  # alle verschieden
