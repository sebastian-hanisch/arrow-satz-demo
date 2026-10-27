"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 2, 5, 2                  # Wähler
M_MIN, M_MAX, DEFAULT_M = 2, 4, 3                  # Alternativen
MAX_VARIABLES = 20000                              # so viele Variablen (Profile × Ausgabeordnungen) darf das Modell höchstens haben
SOLUTION_CAP = 500                                 # so viele Lösungen zählt die Aufzählung höchstens
TIME_LIMIT = 60.0                                  # Sekunden je Lösungsversuch
SAMPLE_PROFILES = 12                               # so viele Profile zeigt die Beispieltabelle
SEED = 0                                           # fester Zufalls-Seed des Lösers (gleiches Modell, gleiches Ergebnis)

DOMAINS = {"alle": "Alle strikten Ordnungen", "einspitzig": "Nur einspitzige Ordnungen"}
DOMAIN_PHRASE = {"alle": "alle strikten Ordnungen", "einspitzig": "nur einspitzige Ordnungen"}
AXIOMS = ("pareto", "iia", "nd")
AXIOM_NAMES = {"pareto": "Pareto", "iia": "Unabhängigkeit irrelevanter Alternativen", "nd": "Nichtdiktatur"}

COLOR_OK, COLOR_NO = "#2F6B65", "#b04a3a"
COLOR_VOTER = ("#4c78a8", "#b04a3a", "#e0a030", "#7f7f7f", "#2F6B65")

# Feste Reihen
SERIES_CASES = ((2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4))
SERIES_COUNT_CASES = ((2, 2), (3, 2), (2, 3), (3, 3), (4, 3), (2, 4))
SERIES_PEAKED_NS = (3, 4, 5)

PRESETS = {
    "Arrow: zwei Wähler, drei Alternativen": {"n": 2, "m": 3, "pareto": True, "iia": True, "nd": True, "domain": "alle"},
    "Drei Wähler, drei Alternativen": {"n": 3, "m": 3, "pareto": True, "iia": True, "nd": True, "domain": "alle"},
    "Ohne Nichtdiktatur": {"n": 3, "m": 3, "pareto": True, "iia": True, "nd": False, "domain": "alle"},
    "Ohne Unabhängigkeit": {"n": 3, "m": 3, "pareto": True, "iia": False, "nd": True, "domain": "alle"},
    "Ohne Pareto": {"n": 3, "m": 3, "pareto": False, "iia": True, "nd": True, "domain": "alle"},
    "Nur zwei Alternativen": {"n": 3, "m": 2, "pareto": True, "iia": True, "nd": True, "domain": "alle"},
    "Einspitzige Ordnungen": {"n": 3, "m": 3, "pareto": True, "iia": True, "nd": True, "domain": "einspitzig"},
    "Handbeispiel: zwei Wähler, zwei Alternativen": {"n": 2, "m": 2, "pareto": True, "iia": True, "nd": True, "domain": "alle"},
}
PRESET_HELP = {
    "Arrow: zwei Wähler, drei Alternativen": "Voreinstellung: zwei Wähler, drei Alternativen, alle strikten Ordnungen, alle drei Axiome. Der Löser meldet aus 216 Variablen (36 Profile mal 6 Ergebnisordnungen), dass es keine Wohlfahrtsfunktion gibt; der gefundene minimale unlösbare Kern hat 9 von 11 Bedingungen (es gibt auch einen mit 8).",
    "Drei Wähler, drei Alternativen": "Dasselbe mit drei Wählern: 216 Profile, 1.296 Variablen, wieder unlösbar; der gefundene minimale Kern hat 10 von 12 Bedingungen (es gibt auch einen mit 9).",
    "Ohne Nichtdiktatur": "Pareto und Unabhängigkeit erlauben bei drei Wählern und drei Alternativen genau drei Wohlfahrtsfunktionen: die drei Diktaturen.",
    "Ohne Unabhängigkeit": "Ohne die Unabhängigkeit irrelevanter Alternativen gibt es viele Lösungen (die Aufzählung bricht bei 500 ab), zum Beispiel eine Rangfolge nach der Summe der Plätze (Borda) mit Gleichstandsbrecher.",
    "Ohne Pareto": "Ohne Pareto sind schon feste Rangfolgen (immer dasselbe Ergebnis) zulässig: ungleich einer Diktatur, unabhängig von den Wählern, aber auch ohne Rücksicht auf einstimmige Wünsche. Die Aufzählung bricht bei 500 ab.",
    "Nur zwei Alternativen": "Mit nur zwei Alternativen sind alle drei Axiome erfüllbar: bei drei Wählern gibt es genau 61 Wohlfahrtsfunktionen (64 mit Pareto und Unabhängigkeit, davon drei Diktaturen).",
    "Einspitzige Ordnungen": "Sind nur einspitzige Ordnungen erlaubt (jede Anfangsstrecke ist ein Abschnitt der Achse A < B < C), sind alle drei Axiome bei drei Wählern und drei Alternativen erfüllbar (allgemein für ungerade Wählerzahl); die Aufzählung bricht bei 500 ab.",
    "Handbeispiel: zwei Wähler, zwei Alternativen": "Von Hand: vier Profile, Pareto legt die zwei einstimmigen fest, bei Uneinigkeit gibt es vier Möglichkeiten, zwei davon sind Diktaturen. Es bleiben genau zwei Wohlfahrtsfunktionen: bei Uneinigkeit gewinnt immer A (oder immer B).",
}
