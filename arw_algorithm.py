"""Kern: Wohlfahrtsfunktionen als Erfüllbarkeitsproblem. Eine Wohlfahrtsfunktion bildet jedes Profil (je Wähler eine strikte Ordnung der m Alternativen) auf eine strikte Ordnung ab. Je Profil p und Ausgabeordnung o gibt es eine
Variable x[p, o] (1: p wird auf o abgebildet), je Profil genau eine davon. Die Axiome sind lineare Bedingungen: Pareto (sind sich alle einig, a vor b zu stellen, tut es auch das Ergebnis), Unabhängigkeit irrelevanter Alternativen (IIA: die
Ordnung eines Paares im Ergebnis hängt nur von der Ordnung dieses Paares bei den Wählern ab) und Nichtdiktatur (es gibt keinen Wähler, dessen Ordnung immer das Ergebnis ist). Gelöst wird mit CP-SAT; ist das Modell unlösbar, liefert ein
Löschverfahren einen kleinsten unlösbaren Kern der Bedingungsgruppen. Ein unabhängiger Prüfer (`check_axioms`) rechnet die Axiome an einer gefundenen Funktion nach der Definition nach."""

import itertools
import time
from dataclasses import dataclass

from ortools.sat.python import cp_model

import arw_constants as C
import arw_scenario as S


def groups_for(n: int, m: int, axioms) -> list:
    """Bedingungsgruppen der gewählten Axiome: Pareto je gerichtetem Paar (a, b), IIA je Paar a < b, Nichtdiktatur je Wähler."""
    groups = []
    if "pareto" in axioms:
        groups += [("pareto", a, b) for a, b in itertools.permutations(range(m), 2)]
    if "iia" in axioms:
        groups += [("iia", a, b) for a, b in itertools.combinations(range(m), 2)]
    if "nd" in axioms:
        groups += [("nd", i, -1) for i in range(n)]
    return groups


def group_text(group) -> str:
    kind, a, b = group
    if kind == "pareto":
        return f"Pareto: {S.name(a)} vor {S.name(b)}"
    if kind == "iia":
        return f"Unabhängigkeit: Paar {S.name(a)}, {S.name(b)}"
    return f"Nichtdiktatur: Wähler {a + 1}"


@dataclass
class Result:
    status: str              # "lösbar", "unlösbar" oder "unbekannt" (Zeitgrenze)
    swf: dict | None         # Profil → Ausgabeordnung (bei "lösbar")
    seconds: float
    profiles: int
    variables: int
    constraints: int


def _build(n: int, m: int, domain: str, groups):
    outs = S.linear_orders(m)
    profs = S.profiles(n, m, domain)
    model = cp_model.CpModel()
    x = {(p, o): model.NewBoolVar("") for p in profs for o in outs}
    for p in profs:
        model.AddExactlyOne([x[p, o] for o in outs])
    for kind, a, b in groups:
        if kind == "pareto":
            for p in profs:
                if all(S.prefers(v, a, b) for v in p):
                    for o in outs:
                        if not S.prefers(o, a, b):
                            model.Add(x[p, o] == 0)
        elif kind == "iia":
            first = {}
            for p in profs:
                key = tuple(S.prefers(v, a, b) for v in p)
                if key in first:
                    q = first[key]
                    model.Add(sum(x[q, o] for o in outs if S.prefers(o, a, b)) == sum(x[p, o] for o in outs if S.prefers(o, a, b)))
                else:
                    first[key] = p
        else:
            model.Add(sum(x[p, p[a]] for p in profs) <= len(profs) - 1)
    return model, x, profs, outs


def _solver(enumerate_all: bool = False):
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = C.SEED
    solver.parameters.max_time_in_seconds = C.TIME_LIMIT
    solver.parameters.enumerate_all_solutions = enumerate_all
    return solver


def solve(n: int, m: int, domain: str, groups) -> Result:
    """Eine Wohlfahrtsfunktion suchen, die alle Gruppen erfüllt."""
    if not S.size_ok(n, m, domain):
        raise ValueError(f"Das Modell hätte mehr als {C.MAX_VARIABLES} Variablen")
    started = time.perf_counter()
    model, x, profs, outs = _build(n, m, domain, groups)
    solver = _solver()
    status = solver.Solve(model)
    seconds = time.perf_counter() - started
    stats = dict(seconds=seconds, profiles=len(profs), variables=len(x), constraints=len(model.Proto().constraints))
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        swf = {p: next(o for o in outs if solver.BooleanValue(x[p, o])) for p in profs}
        return Result("lösbar", swf, **stats)
    if status == cp_model.INFEASIBLE:
        return Result("unlösbar", None, **stats)
    return Result("unbekannt", None, **stats)


def is_feasible(n: int, m: int, domain: str, groups) -> bool:
    return solve(n, m, domain, groups).status == "lösbar"


def enumerate_solutions(n: int, m: int, domain: str, groups, cap: int | None = None):
    """Alle Wohlfahrtsfunktionen, die die Gruppen erfüllen, bis höchstens `cap`. Rückgabe (Liste von Funktionen, vollständig?); vollständig heißt: die Aufzählung ist vor Erreichen der Grenze und der Zeit fertig geworden."""
    cap = C.SOLUTION_CAP if cap is None else cap
    if not S.size_ok(n, m, domain):
        raise ValueError(f"Das Modell hätte mehr als {C.MAX_VARIABLES} Variablen")
    model, x, profs, outs = _build(n, m, domain, groups)
    found = []

    class Collector(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            found.append({p: next(o for o in outs if self.BooleanValue(x[p, o])) for p in profs})
            if len(found) >= cap:
                self.StopSearch()

    status = _solver(enumerate_all=True).Solve(model, Collector())
    return found, status == cp_model.OPTIMAL and len(found) < cap


def minimal_core(n: int, m: int, domain: str, groups):
    """Kleinster unlösbarer Kern der Gruppen (Löschverfahren: jede Gruppe wird entfernt, wenn der Rest unlösbar bleibt); None, wenn die Gruppen erfüllbar sind. Der Kern ist minimal, aber nicht eindeutig."""
    groups = list(groups)
    if is_feasible(n, m, domain, groups):
        return None
    core = list(groups)
    for g in groups:
        rest = [h for h in core if h != g]
        if not is_feasible(n, m, domain, rest):
            core = rest
    return core


def check_axioms(swf: dict, n: int, m: int) -> dict:
    """Prüft die drei Axiome an einer Wohlfahrtsfunktion nach der Definition (Schleifen über Profile, keine Modellrechnung)."""
    profs = list(swf)
    pareto = all(S.prefers(swf[p], a, b) for p in profs for a, b in itertools.permutations(range(m), 2) if all(S.prefers(v, a, b) for v in p))
    iia = True
    for a, b in itertools.combinations(range(m), 2):
        seen = {}                                  # Paarordnung der Wähler → Paarordnung im Ergebnis: Profile mit gleichem Schlüssel müssen gleich antworten
        for p in profs:
            key = tuple(S.prefers(p[i], a, b) for i in range(n))
            value = S.prefers(swf[p], a, b)
            if seen.setdefault(key, value) != value:
                iia = False
    nd = not any(all(swf[p] == p[i] for p in profs) for i in range(n))
    return {"pareto": pareto, "iia": iia, "nd": nd}


def classify(swf: dict, n: int) -> str:
    """Art der Funktion: Diktatur eines Wählers, feste Rangfolge (immer dieselbe Ausgabe) oder andere Regel."""
    profs = list(swf)
    for i in range(n):
        if all(swf[p] == p[i] for p in profs):
            return f"Diktatur von Wähler {i + 1}"
    if len({swf[p] for p in profs}) == 1:
        return "feste Rangfolge"
    return "andere Regel"


def follow_shares(swf: dict, n: int) -> list:
    """Anteil der Profile, in denen das Ergebnis der Ordnung von Wähler i entspricht."""
    profs = list(swf)
    return [sum(1 for p in profs if swf[p] == p[i]) / len(profs) for i in range(n)]
