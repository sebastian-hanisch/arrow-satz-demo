"""Auswertung: Einstellungen, Lösbarkeit der gewählten Axiome, Beispielfunktion, Lösungszahlen, kleinster Kern, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Reihen."""

import math
from collections import Counter
from dataclasses import dataclass

import arw_algorithm as A
import arw_constants as C
import arw_scenario as S


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x, digits: int = 0) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",").replace("-", "−")


def seconds_text(x: float) -> str:
    return f"{x:.2f} s".replace(".", ",") if x < 10 else f"{x:.0f} s"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    pareto: bool = True
    iia: bool = True
    nd: bool = True
    domain: str = "alle"

    def axioms(self) -> tuple:
        return tuple(a for a in C.AXIOMS if getattr(self, a))


@dataclass
class Analysis:
    settings: Settings
    groups: list
    too_big: bool
    result: A.Result | None      # None, wenn das Modell zu groß ist
    count: int                   # Zahl der gefundenen Lösungen (höchstens SOLUTION_CAP)
    complete: bool               # Aufzählung vollständig?
    kinds: dict                  # Art der Lösung → Zahl
    checked: dict | None         # unabhängige Prüfung der Beispielfunktion: Axiom → erfüllt?
    follow: list | None          # Anteil der Profile, in denen das Ergebnis Wähler i folgt


def analyse(settings: Settings) -> Analysis:
    groups = A.groups_for(settings.n, settings.m, settings.axioms())
    if not S.size_ok(settings.n, settings.m, settings.domain):
        return Analysis(settings, groups, True, None, 0, False, {}, None, None)
    result = A.solve(settings.n, settings.m, settings.domain, groups)
    if result.status != "lösbar":
        return Analysis(settings, groups, False, result, 0, True, {}, None, None)
    solutions, complete = A.enumerate_solutions(settings.n, settings.m, settings.domain, groups)
    kinds = dict(Counter(A.classify(s, settings.n) for s in solutions))
    return Analysis(settings, groups, False, result, len(solutions), complete, kinds, A.check_axioms(result.swf, settings.n, settings.m), A.follow_shares(result.swf, settings.n))


def core_of(settings: Settings):
    """Kleinster unlösbarer Kern der gewählten Axiome (None, wenn sie erfüllbar sind oder das Modell zu groß ist)."""
    if not S.size_ok(settings.n, settings.m, settings.domain):
        return None
    return A.minimal_core(settings.n, settings.m, settings.domain, A.groups_for(settings.n, settings.m, settings.axioms()))


# --- Tabellen und Texte ---------------------------------------------------------------------------------------------------------------------

def axiom_text(settings: Settings) -> str:
    chosen = [C.AXIOM_NAMES[a] for a in settings.axioms()]
    return " + ".join(chosen) if chosen else "keine Axiome"


def summary_rows(a: Analysis) -> list:
    if a.result is None:
        return []
    r = a.result
    return [{"Profile": r.profiles, "Variablen": r.variables, "Bedingungen": r.constraints, "Ergebnis": r.status, "Rechenzeit": seconds_text(r.seconds)}]


def sample_indices(total: int, k: int = C.SAMPLE_PROFILES) -> list:
    """Gleichmäßig verteilte Positionen (ohne Wiederholung), höchstens k."""
    if total <= k:
        return list(range(total))
    return sorted({round(i * (total - 1) / (k - 1)) for i in range(k)})


def example_rows(a: Analysis) -> list:
    """Einige Profile der gefundenen Wohlfahrtsfunktion: je Wähler die Ordnung und das Ergebnis."""
    if a.result is None or a.result.swf is None:
        return []
    profs = list(a.result.swf)
    rows = []
    for idx in sample_indices(len(profs)):
        p = profs[idx]
        row = {f"Wähler {i + 1}": S.order_text(p[i]) for i in range(a.settings.n)}
        row["Ergebnis"] = S.order_text(a.result.swf[p])
        rows.append(row)
    return rows


def kind_rows(a: Analysis) -> list:
    return [{"Art der Lösung": k, "Zahl": v} for k, v in sorted(a.kinds.items(), key=lambda kv: (-kv[1], kv[0]))]


def count_text(a: Analysis) -> str:
    return f"genau {a.count}" if a.complete else f"mindestens {a.count}"


def core_rows(core) -> list:
    return [{"Bedingung": A.group_text(g)} for g in core]


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_state(a: Analysis):
    """Kernfrage: gibt es eine Wohlfahrtsfunktion, die alle gewählten Axiome erfüllt? Rückgabe (st-Methode, Text)."""
    s = a.settings
    where = f"{s.n} Wähler, {s.m} Alternativen, {C.DOMAIN_PHRASE[s.domain]}"
    if a.too_big:
        return "info", f"Mit {where} hätte das Modell {S.variable_count(s.n, s.m, s.domain)} Variablen; die Demo rechnet höchstens {C.MAX_VARIABLES}. Weniger Wähler oder Alternativen wählen."
    if a.result.status == "unbekannt":
        return "warning", f"Der Löser hat bei {where} in {C.TIME_LIMIT:.0f} Sekunden keine Antwort gefunden."
    if a.result.status == "unlösbar":
        return "warning", f"Keine Wohlfahrtsfunktion erfüllt {axiom_text(s)} ({where}): der Löser beweist die Unmöglichkeit in {seconds_text(a.result.seconds)} aus {a.result.variables} Variablen."
    only = ""
    if set(a.kinds) <= {k for k in a.kinds if k.startswith("Diktatur")} and a.complete:
        only = " Alle sind Diktaturen."
    return "success", f"Es gibt {count_text(a)} Wohlfahrtsfunktionen, die {axiom_text(s)} erfüllen ({where}).{only} Gefundenes Beispiel: {A.classify(a.result.swf, s.n)}."


# --- Feste Reihen ---------------------------------------------------------------------------------------------------------------------------

VARIANTS = (("alle drei", ("pareto", "iia", "nd")), ("ohne Pareto", ("iia", "nd")), ("ohne Unabhängigkeit", ("pareto", "nd")), ("ohne Nichtdiktatur", ("pareto", "iia")))


def series_cases() -> list:
    """Lösbarkeit je Größe und Axiomauswahl."""
    rows = []
    for n, m in C.SERIES_CASES:
        for label, axioms in VARIANTS:
            r = A.solve(n, m, "alle", A.groups_for(n, m, axioms))
            rows.append({"n": n, "m": m, "variante": label, "status": r.status, "seconds": r.seconds, "variables": r.variables})
    return rows


def series_counts() -> list:
    """Zahl der Wohlfahrtsfunktionen mit Pareto und Unabhängigkeit (ohne Nichtdiktatur) und wie viele davon Diktaturen sind."""
    rows = []
    for n, m in C.SERIES_COUNT_CASES:
        solutions, complete = A.enumerate_solutions(n, m, "alle", A.groups_for(n, m, ("pareto", "iia")))
        dictatorships = sum(1 for s in solutions if A.classify(s, n).startswith("Diktatur"))
        rows.append({"n": n, "m": m, "count": len(solutions), "complete": complete, "dictatorships": dictatorships})
    return rows


def series_domain() -> list:
    """Alle Axiome auf allen Ordnungen gegen einspitzige Ordnungen."""
    rows = []
    for n, m in ((3, 3), (4, 3), (5, 3), (2, 4), (3, 4)):
        for domain in ("alle", "einspitzig"):
            if not S.size_ok(n, m, domain):
                rows.append({"n": n, "m": m, "domain": domain, "status": "zu groß", "seconds": 0.0, "profiles": len(S.domain_orders(m, domain)) ** n})
                continue
            r = A.solve(n, m, domain, A.groups_for(n, m, C.AXIOMS))
            rows.append({"n": n, "m": m, "domain": domain, "status": r.status, "seconds": r.seconds, "profiles": r.profiles})
    return rows


def cases_table(rows) -> list:
    return [{"Wähler": r["n"], "Alternativen": r["m"], "Axiome": r["variante"], "Ergebnis": r["status"], "Variablen": r["variables"], "Rechenzeit": seconds_text(r["seconds"])} for r in rows]


def counts_table(rows) -> list:
    return [{"Wähler": r["n"], "Alternativen": r["m"], "Lösungen mit Pareto und Unabhängigkeit": (f"{r['count']}" if r["complete"] else f"mindestens {r['count']}"), "davon Diktaturen": r["dictatorships"]} for r in rows]


def domain_table(rows) -> list:
    return [{"Wähler": r["n"], "Alternativen": r["m"], "Bereich": C.DOMAINS[r["domain"]], "Profile": r["profiles"], "Ergebnis": r["status"], "Rechenzeit": seconds_text(r["seconds"]) if r["status"] != "zu groß" else "–"} for r in rows]


def verdict_cases(rows):
    """Reihe 1: nur die Kombination aller drei Axiome ist unlösbar."""
    triple_m3 = [r for r in rows if r["variante"] == "alle drei" and r["m"] >= 3]
    relaxed = [r for r in rows if r["variante"] != "alle drei"]
    slowest = max(rows, key=lambda r: r["seconds"])
    text = (f"Alle drei Axiome zusammen sind in allen {len(triple_m3)} Fällen mit mindestens drei Alternativen unlösbar (der Löser braucht dafür höchstens {seconds_text(max(r['seconds'] for r in triple_m3))}); "
            f"jede Lockerung ist lösbar ({sum(1 for r in relaxed if r['status'] == 'lösbar')} von {len(relaxed)} Fällen). Mit zwei Alternativen sind alle drei Axiome erfüllbar. Die längste Rechnung: {slowest['variante']} bei {slowest['n']} Wählern und {slowest['m']} Alternativen ({seconds_text(slowest['seconds'])}).")
    return ("warning" if all(r["status"] == "unlösbar" for r in triple_m3) else "info"), text


def verdict_counts(rows):
    """Reihe 2: mit Pareto und Unabhängigkeit bleiben nur die Diktaturen."""
    big = [r for r in rows if r["m"] >= 3]
    small = [r for r in rows if r["m"] == 2]
    ok = all(r["complete"] and r["count"] == r["n"] == r["dictatorships"] for r in big)
    text = (f"Bei mindestens drei Alternativen gibt es mit Pareto und Unabhängigkeit genau so viele Lösungen wie Wähler, und alle sind Diktaturen ({', '.join(str(r['n']) + ' Wähler, ' + str(r['m']) + ' Alternativen: ' + str(r['count']) for r in big)}). "
            f"Mit zwei Alternativen gibt es mehr: {', '.join(str(r['n']) + ' Wähler: ' + str(r['count']) + ' (davon ' + str(r['dictatorships']) + ' Diktaturen)' for r in small)}.")
    return ("success" if ok else "info"), text


def verdict_domain(rows):
    """Reihe 3: einspitzige Ordnungen sind der Fluchtweg."""
    peaked = [r for r in rows if r["domain"] == "einspitzig"]
    allr = [r for r in rows if r["domain"] == "alle" and r["status"] != "zu groß"]
    text = (f"Auf allen Ordnungen sind die Axiome in allen {len(allr)} gerechneten Fällen unlösbar; auf einspitzigen Ordnungen sind sie in {sum(1 for r in peaked if r['status'] == 'lösbar')} von {len(peaked)} Fällen lösbar "
            f"(bei {max(r['n'] for r in peaked)} Wählern bis {max(r['profiles'] for r in peaked)} Profile).")
    return ("success" if all(r["status"] == "lösbar" for r in peaked) and all(r["status"] == "unlösbar" for r in allr) else "info"), text
