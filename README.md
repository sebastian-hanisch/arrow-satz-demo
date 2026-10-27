# Satz von Arrow: unmöglich per Löser – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-arrow-satz-demo.streamlit.app/)** -->

Gelber Kandidat der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [wahlaxiome-demo](https://github.com/sebastian-hanisch/wahlaxiome-demo) (Axiome und Gegenbeispiele bei bekannten Regeln; die Unmöglichkeit nennt sie ausdrücklich als eigenes Vorhaben), [wahlregeln-demo](https://github.com/sebastian-hanisch/wahlregeln-demo) (Regeln für Präferenzen) und [sat-phasenuebergang-demo](https://github.com/sebastian-hanisch/sat-phasenuebergang-demo) (Erfüllbarkeit als Rechenproblem).
Die Demo fragt: **Eine Gruppe soll aus den Rangfolgen ihrer Mitglieder eine gemeinsame Rangfolge bilden. Der Satz von Arrow sagt, dass ab drei Alternativen keine Regel Pareto, Unabhängigkeit irrelevanter Alternativen und Nichtdiktatur zugleich erfüllt. Lässt sich das für kleine Fälle von einem Löser bestätigen, was bleibt übrig, wenn man ein Axiom lockert, und wann wird es lösbar?** Jede Regel ist eine Antwort auf „welche Ergebnisordnung gehört zu welchem Profil?“; die Axiome sind lineare Bedingungen, und der Löser (CP-SAT) antwortet **lösbar** (mit Beispiel und Zahl der Lösungen) oder **unlösbar** (mit einem minimalen Kern der Bedingungen, die schon genügen).

Der Kern ist eigener Code (Modell, Aufzählung, Löschverfahren für den Kern, Prüfer der Axiome nach der Definition); gelöst wird mit `ortools` (CP-SAT). Unabhängige Orakel in den Tests: die **Aufzählung aller Wohlfahrtsfunktionen** bei zwei Alternativen gegen die Aufzählung des Lösers, ein **zweites Modell mit `scipy` (HiGHS)**, das genau dann lösbar ist, wenn CP-SAT lösbar meldet, **Zeugen von Hand** (Diktatur, feste Rangfolge, Bordafunktion, Mehrheit auf einspitzigen Ordnungen) und der **Satz selbst** (mit Pareto und Unabhängigkeit bleiben genau n Diktaturen).

## Warum dieses Problem

Der Satz von Arrow klingt nach einem Papierbeweis, aber für kleine Fälle ist er ein **Rechenergebnis**: bei zwei Wählern und drei Alternativen gibt es 36 Profile und 6 mögliche Ergebnisordnungen je Profil, also 216 Ja-Nein-Variablen, und der Löser meldet in etwa 0,01 Sekunden (gemessen, rechnerabhängig), dass keine Belegung alle drei Axiome erfüllt. Interessanter als das „Nein“ ist, **was** zusammen unmöglich ist: je zwei der drei Axiome sind erfüllbar (Diktatur, feste Rangfolge, Borda), und mit Pareto und Unabhängigkeit bleiben **genau n Regeln**, die n Diktaturen. Ein **minimaler Kern** (nicht weiter kürzbar, aber nicht der kleinste) zeigt, welche Bedingungen schon genügen: bei drei Alternativen 9 bis 11 der 11 bis 13 Bedingungsgruppen; bei zwei Wählern und drei Alternativen stecken Unabhängigkeit und Nichtdiktatur in allen fünf minimalen Kernen, welche Pareto-Paare dazukommen, hängt vom Kern ab. Und es gibt **Auswege**: nur zwei Alternativen oder nur einspitzige Ordnungen machen die Forderungen erfüllbar.

## Modell

**Profile.** n Wähler, m Alternativen (A, B, …); jeder Wähler gibt eine strikte Ordnung an (m! Möglichkeiten, bei „einspitzig“ nur 2^(m−1)); ein Profil ist die Wahl aller Wähler, es gibt (m!)ⁿ Profile bei allen Ordnungen.
**Wohlfahrtsfunktion.** Ordnet jedem Profil eine strikte Ordnung als Ergebnis zu. Variable x(p, o) ∈ {0, 1}: Profil p wird auf die Ordnung o abgebildet; je Profil genau eine (Profile mal m! Variablen).
**Pareto.** Stehen bei allen Wählern in p die Alternative a vor b, sind alle Ergebnisordnungen mit b vor a verboten.
**Unabhängigkeit irrelevanter Alternativen.** Zwei Profile, in denen jeder Wähler a und b gleich ordnet, müssen a und b im Ergebnis gleich ordnen (Gleichung zwischen Summen von Variablen).
**Nichtdiktatur.** Für jeden Wähler i gibt es mindestens ein Profil, in dem das Ergebnis nicht seiner Ordnung entspricht (Summe der Variablen „Ergebnis = Ordnung von i“ höchstens Profile minus 1).
**Antwort.** CP-SAT mit einem Faden und festem Zufalls-Seed (gleiches Modell, gleiche Antwort). Bei „lösbar“ zählt eine Aufzählung die Lösungen (höchstens 500) und ordnet jede einer Art zu (Diktatur, feste Rangfolge, andere Regel). Bei „unlösbar“ entfernt das **Löschverfahren** nacheinander jede Bedingungsgruppe, wenn der Rest unlösbar bleibt; das Ergebnis ist ein **minimaler** (nicht weiter kürzbarer, nicht eindeutiger) Kern. Das gezeigte Beispiel kann sich mit der OR-Tools-Version ändern; Lösbarkeit und Lösungszahlen nicht. Eine gefundene Funktion wird unabhängig vom Modell nach den Definitionen der Axiome nachgeprüft. Formeln und Lesehilfe stehen im 📐-Expander der App.

## Methodik

- **Kern** (`arw_algorithm.py`): Bedingungsgruppen, Modell, Löser, Aufzählung, minimaler Kern, Prüfer der Axiome, Art der Funktion, Anteil der Profile je Wähler.
- **Szenario und Auswertung** (`arw_scenario.py`, `arw_evaluation.py`): Ordnungen, einspitzige Bereiche, Profile, Größe des Modells; Analyse, Tabellen, drei feste Reihen, alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): acht Schnellstart-Szenarien (eines von Hand), Regler für Wähler und Alternativen, Auswahl des Bereichs, drei Schalter für die Axiome; Ergebnis des Lösers, Beispieltabelle, die ganze Funktion als Gitter bei zwei Wählern, Anteil je Wähler, Arten der Lösungen, minimaler Kern auf Klick, Kernfrage, drei Reiter mit festen Reihen, Annahmen und Formeln. Das Modell darf höchstens 20.000 Variablen haben.

## Befunde (gemessen, keine Behauptungen)

Alle Fälle sind **exakt** gelöst, kein Zufall in der Rechnung. Rechenzeiten sind Messungen auf dem Entwicklungsrechner und hängen vom Rechner ab; die Tests prüfen sie nicht.

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | Bei zwei Alternativen (2 und 3 Wähler) stimmt die Zahl der Lösungen des Lösers für **jede der 8 Axiomauswahlen** mit der **Aufzählung aller Funktionen** (16 und 256) und dem Prüfer überein. Das zweite Modell (HiGHS, eigener Aufbau) meldet für alle 8 Axiomauswahlen genau dann „lösbar“, wenn CP-SAT es tut (5 Größen und Bereiche), und beweist Arrow bei 2 Wählern und 4 Alternativen. Jede gefundene Funktion erfüllt die gewählten Axiome nach der Definition. | `test_oracle_arrow_satz.py` |
| Von Hand: zwei Wähler, zwei Alternativen | Vier Profile; Pareto legt die zwei einstimmigen fest; bei Uneinigkeit gibt es 4 Möglichkeiten, 2 davon Diktaturen: **genau 2 Wohlfahrtsfunktionen** mit allen Axiomen (bei Uneinigkeit gewinnt immer A oder immer B), 4 mit Pareto und Unabhängigkeit. Mit drei Wählern: 2⁶ = 64 mit Pareto und Unabhängigkeit, davon 3 Diktaturen, also **61** mit allen Axiomen. | `test_algorithm.py::test_handbeispiel_genau_zwei_lösungen`, `test_oracle_arrow_satz.py::test_zahlen_der_handbeispiele_von_hand` |
| Welche Kombination ist unmöglich? | Alle drei Axiome: **lösbar** bei 2 Alternativen (2 und 3 Wähler); **unlösbar** bei (2 Wähler, 3 Alternativen) mit 216 Variablen, (3, 3) mit 1.296, (4, 3) mit 7.776 und (2, 4) mit 13.824 (je rund eine Sekunde oder weniger). **Jede Lockerung ist lösbar**: ohne Pareto, ohne Unabhängigkeit oder ohne Nichtdiktatur in allen 18 Fällen (die längste Rechnung: ohne Pareto bei 2 Wählern und 4 Alternativen, etwa 6 bis 7 Sekunden). | `test_claims.py::test_alle_drei_axiome_sind_ab_drei_alternativen_unlösbar`, `…::test_jede_lockerung_ist_lösbar`, `…::test_größen_der_modelle` |
| Wie viele Regeln bleiben? | Mit Pareto und Unabhängigkeit (ohne Nichtdiktatur): bei 3 Alternativen **genau n Lösungen, alle Diktaturen** (2, 3, 4 Wähler: 2, 3, 4; bei 4 Alternativen und 2 Wählern: 2). Bei 2 Alternativen mehr: 4 (davon 2 Diktaturen) bei 2 Wählern, 64 (davon 3) bei 3 Wählern. | `test_claims.py::test_ab_drei_alternativen_bleiben_genau_die_diktaturen`, `…::test_bei_zwei_alternativen_gibt_es_mehr_regeln`, `test_oracle_arrow_satz.py::test_mit_pareto_und_unabhängigkeit_bleiben_genau_die_diktaturen` |
| Welcher Kern genügt? | Minimaler unlösbarer Kern (Löschverfahren in der festen Reihenfolge Pareto, Unabhängigkeit, Nichtdiktatur): **9 von 11** Gruppen bei (2, 3), **10 von 12** bei (3, 3), **11 von 13** bei (4, 3), **14 von 20** bei (2, 4), das ist die Größe des gefundenen Kerns. Er ist nicht weiter kürzbar, aber nicht der kleinste: bei (2, 3) zeigt die Aufzählung aller Teilmengen fünf minimale Kerne mit 8 und 9 Gruppen, und Gegenproben der unabhängigen Prüfung fanden kleinere Kerne mit 9 Gruppen bei (3, 3), 10 bei (4, 3) und 12 bei (2, 4) (nicht in `messen.py`). Bei (2, 3) stecken in allen fünf minimalen Kernen Unabhängigkeit für jedes Paar und Nichtdiktatur für beide Wähler; welche Pareto-Paare dazukommen, hängt vom Kern ab. Im gefundenen Kern stehen Pareto-Gruppen nur für die Paare mit der letzten Alternative (4 von 6 bei drei, 6 von 12 bei vier Alternativen); das ist ein Ergebnis der Löschreihenfolge, keine Aussage über alle Kerne. | `test_algorithm.py::test_kern_ist_unlösbar_und_minimal`, `…::test_kern_enthält_unabhängigkeit_und_beide_nichtdiktaturen` (Fall (2, 3)), `test_evaluation.py::test_hilfetexte_der_presets_stimmen_mit_der_rechnung` ((3, 3)); (4, 3) und (2, 4) nur in `messen.py` (zu langsam für die Tests) |
| Hilft ein engerer Bereich? | Alle Ordnungen: unlösbar bei (3, 3), (4, 3), (2, 4) (bei (5, 3) und (3, 4) zu groß). **Einspitzige Ordnungen** (4 Ordnungen bei drei, 8 bei vier Alternativen): **lösbar** in allen 5 Fällen, bis 5 Wähler (1.024 Profile) und bis 3 Wähler bei 4 Alternativen (512 Profile). Die Mehrheitsrelation selbst erfüllt auf einspitzigen Ordnungen alle drei Axiome (3 und 5 Wähler; allgemein ist das für ungerade Wählerzahl bekannt, für die gerechneten Größen ist die Forderung lösbar). | `test_claims.py::test_alle_ordnungen_unlösbar_einspitzig_lösbar`, `test_oracle_arrow_satz.py::test_mehrheit_auf_einspitzigen_ordnungen_erfüllt_alle_axiome` |
| Zeugen von Hand | Diktatur: Pareto und Unabhängigkeit erfüllt, Nichtdiktatur verletzt. Feste Rangfolge: nur Pareto verletzt. **Bordafunktion** (Summe der Plätze, bei Gleichstand die kleinere Alternative): nur Unabhängigkeit verletzt, zum Beispiel bei zwei Wählern mit A und B gleich geordnet, aber verschiedenem Platz von C (Summen 1 und 1 gegen 2 und 1). Der Condorcet-Zyklus zeigt, dass die Mehrheit auf allen Ordnungen keine Ordnung liefert. | `test_oracle_arrow_satz.py::test_zeugen_erfüllen_genau_die_erwarteten_axiome`, `test_algorithm.py::test_prüfer_iia_konkretes_gegenbeispiel_der_bordafunktion` |
| Schnellstart-Szenarien | Acht Szenarien; Hilfetexte mit den Zahlen oben (216 und 1.296 Variablen, 9 von 11 und 10 von 12, genau 3 Diktaturen, 61 Lösungen bei drei Wählern und zwei Alternativen, genau 2 im Handbeispiel). | `test_evaluation.py::test_hilfetexte_der_presets_stimmen_mit_der_rechnung` |
| Vormessung | Eine Vormessung vor dem Bau (Wegwerfskript, derselbe Aufbau) zeigte denselben Sinn und dieselben Kerne (9 von 11, 10 von 12); **keine Zahl daraus** steht hier, alle Zahlen sind die der festen Reihen der Demo. | – |

## Ehrliche Grenzen

- **Ergebnis ist eine strikte Ordnung.** Arrows Satz gilt auch für Ergebnisse mit Gleichstand (schwache Ordnungen); hier sind nur strikte Ordnungen zugelassen. Das ist ein engeres Modell: Die Unmöglichkeit gilt dort erst recht, aber die Zahlen („genau n Lösungen“, 61 und 64 bei zwei Alternativen) gelten nur für strikte Ergebnisse.
- **Kleine Fälle.** Der Löser meldet die Unmöglichkeit nur für die gerechneten Größen (höchstens 20.000 Variablen: (2, 3), (3, 3), (4, 3), (2, 4) und kleinere), gegengeprüft mit einem zweiten Modell, ohne geprüftes Beweiszertifikat; der allgemeine Satz braucht einen Beweis auf Papier. Dass ein Löser bei größeren Fällen nicht mehr mitkommt, ist kein Gegenbeispiel.
- **Alle Ordnungen kommen vor** ist selbst eine Annahme; der Ausweg „einspitzig“ zeigt, dass es an ihr hängt.
- **Rein ordinal.** Verfahren, die Stärken der Meinung berücksichtigen (siehe `quadratisches-waehlen-demo`), verlassen Arrows Rahmen.
- **Der Kern ist nicht eindeutig.** Das Löschverfahren liefert einen minimalen Kern in der Reihenfolge der Gruppen, nicht den kleinsten (bei (2, 3) gibt es einen mit 8 statt 9 Gruppen); andere minimale Kerne sehen anders aus. Er ist minimal (nach der Meldung des Lösers ist jede Gruppe nötig), nicht der einzige.
- **Aufzählung bis 500.** Bei vielen Lösungen bricht sie ab; „mindestens 500“ ist eine Untergrenze, kein Befund über die Gesamtzahl.
- **Rechenzeiten sind Messungen** auf einem Rechner und hängen von ihm ab; der Löser läuft mit einem Faden.
- **Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Arrow, „Social Choice and Individual Values“, 1951; Geanakoplos, „Three Brief Proofs of Arrow’s Impossibility Theorem“, 2005; Tang und Lin, „A Computer-Aided Proof of Arrow’s Theorem“, Artificial Intelligence 2009; Black, „On the Rationale of Group Decision-making“, 1948.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9203, Präfix `arw_`. Der Ordner heißt `arrow-satz-demo`.
- **Plan:** „die Unmöglichkeit für kleine Fälle (zwei Wähler, drei Kandidaten) mit einem SAT-Löser beweisen; höchstens Tab in Stück 2“. Umgesetzt als eigene Demo mit CP-SAT statt eines reinen SAT-Lösers, weil sich Pareto, Unabhängigkeit und Nichtdiktatur als lineare Bedingungen kompakt ausdrücken lassen; ein zweites Modell mit HiGHS prüft die Aussage gegen.
- **Größengrenze:** der Entwurf nahm 60.000 Variablen an; bei (5, 3) mit allen Ordnungen brauchte der Löser aber etwa 6,5 Sekunden, und der Kern hätte Minuten gedauert. Die Grenze liegt jetzt bei **20.000 Variablen**, größere Fälle meldet die App als zu groß.
- **Kern auf Klick:** das Löschverfahren braucht bei (4, 3) etwa 12 und bei (2, 4) etwa 21 Sekunden; die App rechnet ihn deshalb erst auf Klick.
- **Reglerspanne:** Wähler 2 bis 5, Alternativen 2 bis 4 (der größte erlaubte Fall mit allen Ordnungen ist (4, 3); mit einspitzigen Ordnungen gehen (5, 3) und (3, 4)).
- **Prüfer in Linearzeit:** der erste Prüfer der Unabhängigkeit verglich alle Paare von Profilen (quadratisch in der Zahl der Profile) und brauchte bei (4, 3) mehrere Sekunden je Funktion; jetzt wird nach der Paarordnung der Wähler gruppiert, mit demselben Ergebnis (Oraklen und Zeugen unverändert grün).
- **Tests:** die Randfallreihe über alle Axiomauswahlen läuft nur für kleine Größen; die großen Fälle laufen in Orakeln und Reihen (ein erster Entwurf mit allen Größen brauchte über zwei Minuten je Fall).

## Verifikation

- **Umfang:** 140 Tests.
- **Kern:** jede Einheit an Mini-Fällen (Bedingungsgruppen, Gruppentexte, Prüfer an Diktatur, fester Rangfolge und Bordafunktion, konkretes Gegenbeispiel zur Unabhängigkeit, Aufzählung an der Grenze, Zeitgrenze, minimaler Kern und seine Minimalität).
- **Orakel:** Aufzählung aller Funktionen, zweites Modell mit HiGHS, Zeugen von Hand, der Satz (siehe Befunde).
- **Reihen und Texte:** jede Zahl dieser README in `tests/test_claims.py` und `tests/test_evaluation.py` (Hilfetexte der Presets, Verdikte und Tabellen als reine Funktionen), Randfälle und Adresszeile in `tests/test_edge_cases.py`.
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe); Schalter und Auswahlfeld gehören zu den geprüften Reglern.
- **Mutationsprüfung** (`tools/mutate_demo.py`): 36 Stellen in Kern und Auswertung (`arw_algorithm.py`, `arw_evaluation.py`), **35 gefangen** (1 davon über eine wortgleiche Zeile in einer Nachbar-Demo), keine äquivalente, keine Zeitüberschreitung. Der erste Lauf ließ 4 überleben; **echte Lücken** waren: die Prüfung der Unabhängigkeit beim letzten Alternativenpaar, die Meldung „vollständig“ an der Grenze der Aufzählung und bei abgebrochener Suche, und vorzeichenrichtig gemessene Rechenzeit (je ein neuer Test).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `arw_algorithm.py` | Kern: Modell, Löser, Aufzählung, minimaler Kern, Prüfer der Axiome |
| `arw_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `arw_evaluation.py` | Analyse, Tabellen, Verdikte, drei feste Reihen |
| `arw_layout.py` | Fester Kopf (Stylesheet) |
| `arw_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben) |
| `arw_scenario.py` | Alternativen, Ordnungen, Bereiche, Profile |
| `arw_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (zweites Modell) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Kern, Orakel, Reihen und Claims, Auswertung und Presets, Randfälle, Szenario, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Schwache Ordnungen als Ergebnis** (Gleichstände erlaubt): ein eigenes, größeres Modell.
- **Größere Fälle** (mehr Wähler oder Alternativen mit allen Ordnungen): die Variablenzahl wächst mit (m!)ⁿ.
- **Ein Beweis in lesbarer Form** (die Argumentation der Kurzbeweise): die Demo zeigt nur einen minimalen Kern der Bedingungen, nicht den Schluss.
- **Andere Unmöglichkeitssätze** (Gibbard–Satterthwaite, Sen): jeweils ein eigenes Thema.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und OR-Tools (SciPy nur in den Tests).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
