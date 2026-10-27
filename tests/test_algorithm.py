"""Kern: Bedingungsgruppen, Löser, Aufzählung, kleinster Kern, Prüfer der Axiome, Art der Funktion. Jede Einheit an Mini-Fällen mit Handrechnung (DEMO-PLAYBOOK §1b)."""

from types import SimpleNamespace

import pytest
from ortools.sat.python import cp_model

import arw_algorithm as A
import arw_constants as C
import arw_scenario as S

ALL = ("pareto", "iia", "nd")


def dictator(n, m, i, domain="alle"):
    return {p: p[i] for p in S.profiles(n, m, domain)}


def constant(n, m, domain="alle"):
    return {p: S.linear_orders(m)[0] for p in S.profiles(n, m, domain)}


def borda(n, m, domain="alle"):
    """Rangfolge nach der Summe der Plätze (kleiner ist besser), bei Gleichstand die kleinere Alternative zuerst."""
    swf = {}
    for p in S.profiles(n, m, domain):
        score = {a: sum(v.index(a) for v in p) for a in range(m)}
        swf[p] = tuple(sorted(range(m), key=lambda a: (score[a], a)))
    return swf


# --- Bedingungsgruppen ------------------------------------------------------------------------------------------------------------------------


def test_gruppen_je_axiom():
    assert len(A.groups_for(2, 3, ALL)) == 6 + 3 + 2 == 11 and len(A.groups_for(3, 3, ALL)) == 12 and len(A.groups_for(2, 4, ALL)) == 12 + 6 + 2
    assert A.groups_for(2, 3, ("pareto",)) == [("pareto", a, b) for a in range(3) for b in range(3) if a != b]
    assert A.groups_for(2, 3, ("iia",)) == [("iia", 0, 1), ("iia", 0, 2), ("iia", 1, 2)]
    assert A.groups_for(3, 3, ("nd",)) == [("nd", 0, -1), ("nd", 1, -1), ("nd", 2, -1)] and A.groups_for(2, 3, ()) == []
    assert A.groups_for(2, 2, ALL)[-3:] == [("iia", 0, 1), ("nd", 0, -1), ("nd", 1, -1)]                           # Reihenfolge: Pareto, IIA, Nichtdiktatur


def test_gruppentexte():
    assert A.group_text(("pareto", 0, 2)) == "Pareto: A vor C" and A.group_text(("iia", 1, 2)) == "Unabhängigkeit: Paar B, C" and A.group_text(("nd", 1, -1)) == "Nichtdiktatur: Wähler 2"


# --- Prüfer der Axiome ------------------------------------------------------------------------------------------------------------------------


def test_prüfer_diktatur():
    assert A.check_axioms(dictator(2, 3, 0), 2, 3) == {"pareto": True, "iia": True, "nd": False}
    assert A.check_axioms(dictator(3, 3, 2), 3, 3) == {"pareto": True, "iia": True, "nd": False}


def test_prüfer_feste_rangfolge_verletzt_nur_pareto():
    assert A.check_axioms(constant(2, 3), 2, 3) == {"pareto": False, "iia": True, "nd": True}


def test_prüfer_borda_verletzt_nur_die_unabhängigkeit():
    assert A.check_axioms(borda(3, 3), 3, 3) == {"pareto": True, "iia": False, "nd": True}
    assert A.check_axioms(borda(2, 3), 2, 3) == {"pareto": True, "iia": False, "nd": True}


def test_prüfer_einzelne_verletzung_wird_gefunden():
    swf = dictator(2, 2, 0)
    assert A.check_axioms(swf, 2, 2)["nd"] is False
    swf[((0, 1), (0, 1))] = (1, 0)                                                      # gegen die Einstimmigkeit
    assert A.check_axioms(swf, 2, 2)["pareto"] is False
    swf2 = {((0, 1), (0, 1)): (0, 1), ((0, 1), (1, 0)): (0, 1), ((1, 0), (0, 1)): (1, 0), ((1, 0), (1, 0)): (1, 0)}      # Wähler 1 diktiert: IIA erfüllt
    assert A.check_axioms(swf2, 2, 2) == {"pareto": True, "iia": True, "nd": False}
    swf3 = {((0, 1), (0, 1)): (0, 1), ((0, 1), (1, 0)): (0, 1), ((1, 0), (0, 1)): (0, 1), ((1, 0), (1, 0)): (1, 0)}      # bei Uneinigkeit immer A: kein Diktator
    assert A.check_axioms(swf3, 2, 2) == {"pareto": True, "iia": True, "nd": True}


def test_prüfer_iia_konkretes_gegenbeispiel_der_bordafunktion():
    # Beide Wähler ordnen A und B in p und q gleich (Wähler 1: A vor B, Wähler 2: B vor A); nur C wandert. Summen der Plätze: p: A 1, B 1 (Gleichstand: A zuerst), q: A 2, B 1 (B zuerst).
    swf = borda(2, 3)
    p, q = ((0, 1, 2), (1, 0, 2)), ((0, 1, 2), (1, 2, 0))
    assert all(S.prefers(p[i], 0, 1) == S.prefers(q[i], 0, 1) for i in range(2))
    assert S.prefers(swf[p], 0, 1) and not S.prefers(swf[q], 0, 1)
    assert A.check_axioms(swf, 2, 3)["iia"] is False


def test_art_der_funktion():
    assert A.classify(dictator(3, 3, 1), 3) == "Diktatur von Wähler 2" and A.classify(dictator(2, 2, 0), 2) == "Diktatur von Wähler 1"
    assert A.classify(constant(2, 3), 2) == "feste Rangfolge" and A.classify(borda(3, 3), 3) == "andere Regel"


def test_anteil_der_profile_je_wähler():
    assert A.follow_shares(dictator(2, 3, 0), 2) == [1.0, pytest.approx(1 / 6)]                   # Wähler 2 stimmt in einem Sechstel zufällig überein
    assert A.follow_shares(constant(2, 2), 2) == [0.5, 0.5]


# --- Löser ------------------------------------------------------------------------------------------------------------------------------------


def test_arrow_zwei_wähler_drei_alternativen_ist_unlösbar():
    r = A.solve(2, 3, "alle", A.groups_for(2, 3, ALL))
    assert r.status == "unlösbar" and r.swf is None and (r.profiles, r.variables) == (36, 216) and r.constraints > 36 and r.seconds >= 0


@pytest.mark.parametrize("drop", ["pareto", "iia", "nd"])
def test_jede_lockerung_ist_lösbar_und_die_antwort_erfüllt_die_übrigen_axiome(drop):
    axioms = tuple(a for a in ALL if a != drop)
    r = A.solve(3, 3, "alle", A.groups_for(3, 3, axioms))
    assert r.status == "lösbar" and len(r.swf) == 216
    checked = A.check_axioms(r.swf, 3, 3)
    assert all(checked[a] for a in axioms)


def test_zwei_alternativen_erfüllen_alle_axiome():
    r = A.solve(3, 2, "alle", A.groups_for(3, 2, ALL))
    assert r.status == "lösbar" and A.check_axioms(r.swf, 3, 2) == {"pareto": True, "iia": True, "nd": True}


def test_einspitzige_ordnungen_erfüllen_alle_axiome():
    r = A.solve(3, 3, "einspitzig", A.groups_for(3, 3, ALL))
    assert r.status == "lösbar" and len(r.swf) == 64 and A.check_axioms(r.swf, 3, 3) == {"pareto": True, "iia": True, "nd": True}


def test_ohne_axiome_ist_jede_funktion_zulässig():
    r = A.solve(2, 3, "alle", [])
    assert r.status == "lösbar" and len(r.swf) == 36


def test_antwort_ist_bei_gleichem_modell_gleich():
    g = A.groups_for(3, 3, ("pareto", "nd"))
    assert A.solve(3, 3, "alle", g).swf == A.solve(3, 3, "alle", g).swf


def test_zu_großes_modell_wird_abgelehnt():
    with pytest.raises(ValueError):
        A.solve(5, 3, "alle", [])
    with pytest.raises(ValueError):
        A.enumerate_solutions(3, 4, "alle", [])


def test_zeitgrenze_ergibt_unbekannt(monkeypatch):
    fake = SimpleNamespace(parameters=SimpleNamespace(), Solve=lambda model, *args: cp_model.UNKNOWN)
    monkeypatch.setattr(A, "_solver", lambda enumerate_all=False: fake)
    r = A.solve(2, 2, "alle", [])
    assert r.status == "unbekannt" and r.swf is None


def test_ist_lösbar():
    assert A.is_feasible(2, 2, "alle", A.groups_for(2, 2, ALL)) and not A.is_feasible(2, 3, "alle", A.groups_for(2, 3, ALL))


def test_solver_parameter(monkeypatch):
    s = A._solver()
    assert s.parameters.num_workers == 1 and s.parameters.random_seed == C.SEED and s.parameters.max_time_in_seconds == C.TIME_LIMIT and not s.parameters.enumerate_all_solutions
    assert A._solver(True).parameters.enumerate_all_solutions


# --- Aufzählung -------------------------------------------------------------------------------------------------------------------------------


def test_handbeispiel_genau_zwei_lösungen(two_two):
    n, m = two_two
    sols, complete = A.enumerate_solutions(n, m, "alle", A.groups_for(n, m, ALL))
    assert complete and len(sols) == 2
    mixed = [((0, 1), (1, 0)), ((1, 0), (0, 1))]
    outputs = sorted(tuple(s[p] for p in mixed) for s in sols)
    assert outputs == [((0, 1), (0, 1)), ((1, 0), (1, 0))]                                # bei Uneinigkeit immer A vorn oder immer B vorn
    for s in sols:
        assert s[((0, 1), (0, 1))] == (0, 1) and s[((1, 0), (1, 0))] == (1, 0)


def test_aufzählung_ohne_nichtdiktatur_sind_genau_die_diktaturen():
    sols, complete = A.enumerate_solutions(3, 3, "alle", A.groups_for(3, 3, ("pareto", "iia")))
    assert complete and sorted(A.classify(s, 3) for s in sols) == ["Diktatur von Wähler 1", "Diktatur von Wähler 2", "Diktatur von Wähler 3"]


def test_aufzählung_zählt_bis_zur_grenze_und_meldet_unvollständigkeit():
    sols, complete = A.enumerate_solutions(3, 3, "alle", A.groups_for(3, 3, ("iia", "nd")), cap=7)
    assert len(sols) == 7 and not complete and len({tuple(sorted(s.items())) for s in sols}) == 7
    sols, complete = A.enumerate_solutions(2, 2, "alle", A.groups_for(2, 2, ALL), cap=1)
    assert len(sols) == 1 and not complete                                                  # genau an der Grenze: nicht als vollständig gemeldet
    sols, complete = A.enumerate_solutions(2, 2, "alle", A.groups_for(2, 2, ALL), cap=3)
    assert len(sols) == 2 and complete
    default = A.enumerate_solutions(2, 2, "alle", A.groups_for(2, 2, ALL))
    assert len(default[0]) == 2 and C.SOLUTION_CAP == 500


# --- Kleinster Kern ---------------------------------------------------------------------------------------------------------------------------


def test_kern_ist_unlösbar_und_minimal():
    groups = A.groups_for(2, 3, ALL)
    core = A.minimal_core(2, 3, "alle", groups)
    assert core is not None and set(core) <= set(groups) and len(core) == 9
    assert not A.is_feasible(2, 3, "alle", core)
    for g in core:
        assert A.is_feasible(2, 3, "alle", [h for h in core if h != g])                      # jede Gruppe ist nötig
    assert core == A.minimal_core(2, 3, "alle", groups)                                      # deterministisch


def test_kern_enthält_unabhängigkeit_und_beide_nichtdiktaturen():
    core = A.minimal_core(2, 3, "alle", A.groups_for(2, 3, ALL))
    assert [("iia", 0, 1), ("iia", 0, 2), ("iia", 1, 2), ("nd", 0, -1), ("nd", 1, -1)] == [g for g in core if g[0] != "pareto"]
    assert len([g for g in core if g[0] == "pareto"]) == 4                                   # Pareto nur für vier der sechs gerichteten Paare


def test_kein_kern_bei_erfüllbaren_bedingungen():
    assert A.minimal_core(3, 3, "alle", A.groups_for(3, 3, ("pareto", "iia"))) is None
    assert A.minimal_core(2, 2, "alle", A.groups_for(2, 2, ALL)) is None


# --- Lücken aus der Mutationsprüfung ---------------------------------------------------------------------------------------------------------


def test_prüfer_findet_verletzung_der_unabhängigkeit_auch_beim_letzten_alternativenpaar():
    # Diktatur von Wähler 1, aber im Profil p ist das Ergebnis (A, C, B) statt (A, B, C): nur das Paar (B, C) kippt gegenüber q, in dem beide Wähler B vor C stellen
    swf = dictator(2, 3, 0)
    p, q = ((0, 1, 2), (0, 1, 2)), ((1, 0, 2), (0, 1, 2))
    swf[p] = (0, 2, 1)
    assert all(S.prefers(p[i], 1, 2) == S.prefers(q[i], 1, 2) for i in range(2)) and S.prefers(swf[q], 1, 2) and not S.prefers(swf[p], 1, 2)
    assert A.check_axioms(swf, 2, 3)["iia"] is False


def test_aufzählung_genau_an_der_grenze_gilt_nicht_als_vollständig():
    sols, complete = A.enumerate_solutions(2, 2, "alle", A.groups_for(2, 2, ALL), cap=2)
    assert len(sols) == 2 and not complete


def test_abgebrochene_aufzählung_ist_nicht_vollständig(monkeypatch):
    monkeypatch.setattr(C, "TIME_LIMIT", 0.05)
    sols, complete = A.enumerate_solutions(3, 3, "alle", A.groups_for(3, 3, ("iia", "nd")), cap=10**6)
    assert 0 <= len(sols) < 10**6 and not complete                                              # die Zeitgrenze beendet die Suche vor dem Ende der Aufzählung


def test_rechenzeit_ist_die_dauer_des_aufbaus_und_der_lösung():
    r = A.solve(2, 3, "alle", A.groups_for(2, 3, ALL))
    assert 0 <= r.seconds < 30
