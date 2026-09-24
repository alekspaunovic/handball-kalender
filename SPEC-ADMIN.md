# Erweiterung: Admin-Oberfläche für manuelle Eingriffe

Ergänzung zur bestehenden SPEC.md. Alles Beschriebene kommt zum laufenden
Projekt hinzu, ohne dessen Grundaufbau zu ändern.

## 1. Zweck

Das Skript baut die Feeds bei jedem Lauf vollständig aus den Quellen neu.
Manuelle Eingriffe müssen deshalb als eigene Datenschicht existieren, die bei
jedem Lauf mitgelesen wird. Ein im Kalender gelöschter Termin wäre sonst beim
nächsten Lauf wieder da.

Drei Eingriffe sollen möglich sein:

- einzelne Termine aus den eigenen Feeds ausblenden
- eigene Termine anlegen, die in keiner Quelle stehen
- einzelne Spiele fremder Mannschaften (A-Jugend, 1. Herren, 1. Damen)
  freischalten

Bedient wird das über eine Weboberfläche, die neben den Feeds auf GitHub Pages
liegt. Kein Server, keine Datenbank.

## 2. Neue Dateien

| Datei | Zweck | Wer schreibt |
| --- | --- | --- |
| `overrides.json` | Sperrliste, eigene Termine, freigeschaltete Fremdspiele | die App |
| `docs/pool.json` | alle bekannten Termine als Auswahlgrundlage | der Workflow |
| `docs/admin/index.html` | die Oberfläche | einmalig beim Bau |

### overrides.json

```json
{
  "version": 1,
  "hidden": ["tbw-m2-spiel-380455"],
  "custom": [
    {
      "uid": "tbw-custom-a1b2c3",
      "summary": "Mannschaftsabend",
      "dtstart": "2026-11-14T19:00:00",
      "dtend": "2026-11-14T23:00:00",
      "all_day": false,
      "location": "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland",
      "description": "",
      "created": "2026-09-24T18:00:00Z"
    }
  ],
  "included": ["tbw-a-jugend-spiel-661234"]
}
```

- `hidden`: UIDs, die nicht in den Feed geschrieben werden
- `custom`: eigene Termine, landen im Extra-Feed
- `included`: UIDs aus dem Pool fremder Teams, landen im Extra-Feed

Die UIDs eigener Termine bekommen das Präfix `tbw-custom-` und eine zufällige
Kennung. Sie bleiben stabil, damit der Kalender bearbeitet statt dupliziert.

### docs/pool.json

Wird bei jedem Workflow-Lauf neu geschrieben und enthält alle Termine, die das
Skript gesehen hat, auch die der Fremdteams:

```json
{
  "generated": "2026-09-24T06:00:00Z",
  "halls": [
    {
      "name": "Sporthalle Fliethe",
      "address": "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland"
    }
  ],
  "events": [
    {
      "uid": "tbw-a-jugend-spiel-661234",
      "team": "A-Jugend",
      "team_key": "a-jugend",
      "own_team": false,
      "type": "spiele",
      "summary": "A-Jugend Heim TV Ratingen",
      "dtstart": "2026-10-05T16:00:00+02:00",
      "dtend": "2026-10-05T17:15:00+02:00",
      "all_day": false,
      "location": "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland",
      "cancelled": false
    }
  ]
}
```

`team_key` und `type` stehen dort, weil die Oberfläche die Teamfarbe und die
Unterscheidung Spiel/Training an der linken Kante der Zeile zeigt (Abschnitt 6)
und beides nicht aus dem Titel geraten soll. `dtend` und `all_day` braucht sie,
um Ganztagestermine ohne Uhrzeitspalte darzustellen.

Der Pool entsteht aus den Archiven, nicht aus den Quellen. Er enthält deshalb
auch ausgeblendete Termine -- sonst ließe sich ein Ausblenden nicht wieder
zurücknehmen.

`halls` trägt die Hallenliste für die Ortsauswahl im Formular mit. `halls.yaml`
liegt im Wurzelverzeichnis und ist über GitHub Pages nicht erreichbar -- also
dieselbe Begründung, aus der der Pool überhaupt existiert.

Das ist nötig, weil ein Browser die Spielpläne von handball.net nicht direkt
abrufen darf. Die Sicherheitsregeln fremder Webseiten verhindern das. Der
Workflow bereitet die Liste deshalb vor.

## 3. Neue Quellen

In `config.yaml` kommen drei Teams hinzu, die nur für den Pool gelesen und nie
automatisch in einen Feed geschrieben werden:

| Team | Kürzel | Quelle | Rolle |
| --- | --- | --- | --- |
| A-Jugend | `a-jugend` | https://www.handball.net/kalender/team/94756.ics | nur Pool |
| 1. Herren | `1-herren` | https://www.handball.net/kalender/team/75787.ics | nur Pool |
| 1. Damen | `1-damen` | https://www.handball.net/kalender/team/76182.ics | nur Pool |

Das Kürzel steckt in der UID (`tbw-a-jugend-spiel-661234`) und ändert sich
deshalb nie. Auch diese drei Teams führen ein Archiv unter `data/`, wie die
eigenen Feeds. Nur so bleibt ein freigeschaltetes Fremdspiel im Extra-Feed
stehen, wenn es aus dem rollierenden Quellfenster fällt, und nur so greift die
Verschwinden-Logik aus SPEC.md Abschnitt 7 auch für sie.

Für diese Teams gilt die Treffpunkt-Logik nicht, sie sind reine
Zuschauertermine. Die Heim-Auswärts-Erkennung und die Adressbereinigung greifen
dagegen wie bei den eigenen Teams, damit Titel und Navigation stimmen.

Eigenname für die Gegnererkennung: aus dem `X-WR-CALNAME` des jeweiligen Feeds
lesen, wie bei den eigenen Teams auch.

## 4. Neuer Feed

`docs/extra.ics`, Kalendername `TBW Extra`.

Inhalt: alle Einträge aus `custom` und alle über `included` freigeschalteten
Fremdspiele. Wird wie die anderen Feeds abonniert.

Es bleibt bei einem einzelnen Feed für beides. Zwei getrennte Feeds wären nur
dann im Vorteil, wenn die Zuschauertermine regelmäßig am Stück ausgeblendet
werden sollen; das ist nicht der Fall, und der Preis wäre ein zweites Abonnement
auf jedem Gerät.

Freigeschaltete Fremdspiele bleiben an ihre Quelle gekoppelt. Verlegt der
Verband ein Spiel, verschiebt sich der Termin mit. Wird es zurückgezogen,
greift die normale Absage-Logik inklusive ABGESAGT-Präfix.

## 5. Ablauf im Skript

Nach der bisherigen Transformation und dem Archiv-Abgleich, vor dem Schreiben
der Feeds:

1. `overrides.json` laden. Fehlt die Datei oder ist sie fehlerhaft, mit leeren
   Listen weiterarbeiten und eine Warnung loggen. Die Feeds müssen auch dann
   entstehen.
2. Alle Termine aus `hidden` aus den Team-Feeds entfernen.
3. Pool aus allen bekannten Terminen bilden und nach `docs/pool.json`
   schreiben.
4. Extra-Feed bauen aus `custom` plus den über `included` ausgewählten
   Pool-Einträgen.
5. Alle Feeds schreiben.

Das Archiv bleibt unberührt. Ein ausgeblendeter Termin wird nicht gelöscht,
nur nicht ausgegeben. Deshalb ist jedes Ausblenden umkehrbar.

## 6. Die Oberfläche

Eine einzelne HTML-Datei unter `docs/admin/index.html`, ohne Framework und ohne
Abhängigkeiten von fremden Servern. Schriften über Google Fonts sind erlaubt,
brauchen aber einen echten Fallback-Stack.

Die Oberfläche wird zu 90 Prozent auf dem iPhone benutzt, oft kurz vor oder
nach dem Training. Sie wird deshalb für den Daumen entworfen und am Desktop
verbreitert, nicht umgekehrt.

### Gestaltungsrichtung

Das Gegenmodell ist die typische Verwaltungsoberfläche: graue Tabelle, kleine
Schaltflächen, alles gleich wichtig. Die App hat genau eine Aufgabe, nämlich
Termine an- und abzuschalten. Das soll sie so selbstverständlich können wie
eine Einkaufsliste.

Leitgedanken:

- Der Terminplan ist das Interface. Keine Kacheln, keine Kästen um jede Zeile,
  keine Schatten. Die Liste selbst trägt die Gestaltung, über Rhythmus,
  Ausrichtung und Typografie.
- Ein Blick soll reichen, um Spiel von Training und eigenes Team von fremdem
  Team zu unterscheiden. Dafür ist die linke Kante der Zeile zuständig, nicht
  ein Etikett im Text.
- Der Zustand ist das Wichtigste auf dem Bildschirm. Ein ausgeblendeter Termin
  muss durchgestrichen und deutlich zurückgenommen wirken, ein
  freigeschalteter Fremdtermin sichtbar aktiv.
- Sparsam mit Farbe. Die Teamfarben sind das einzige bunte Element, alles
  andere ist ruhig.

Bewusst nicht erwünscht, weil es nach Standardvorlage aussieht: Kachelraster
mit gleichen Rundungen und weichen Schatten, Großbuchstaben-Etiketten über
jeder Überschrift, Verlaufsflächen als Dekoration, Pfeile hinter
Schaltflächentexten, Einblendanimationen bei jedem Abschnitt.

### Aufbau

Kopfbereich, beim Scrollen fixiert und schmal:

- links der Zeitraumfilter als Auswahlfeld
- rechts der Speichern-Knopf, der nur erscheint, wenn es etwas zu speichern
  gibt

Darunter die drei Bereiche. Auf dem Handy als Reiterleiste am unteren
Bildschirmrand, damit sie mit dem Daumen erreichbar ist. Am Desktop als
Navigation an der Seite.

Die Liste ist nach Datum gruppiert. Das Datum steht als Zwischenüberschrift,
nicht in jeder Zeile. Eine Terminzeile enthält:

```
│  19:00   Training 3. Herren                        ◯
│          Sporthalle Fliethe
```

Die senkrechte Linie links trägt die Teamfarbe und ist bei Spielen kräftiger
als bei Trainings. Die Uhrzeit steht in einer eigenen Spalte, links
ausgerichtet, damit die Zeiten untereinander eine lesbare Kante bilden. Der
Schalter sitzt rechts.

Ausgeblendete Termine: Text durchgestrichen, Deckkraft reduziert, Farblinie
links entsättigt. Sie bleiben an ihrer Stelle in der Liste stehen.

### Zustände

Leere Liste: eine Zeile in ganzen Sätzen, die sagt, was zu tun ist. Also bei
den Fremdteams nicht "Keine Daten", sondern der Hinweis, dass hier Spiele der
A-Jugend, 1. Herren und 1. Damen stehen und jedes einzeln in den Kalender
geholt werden kann.

Ladezustand: Die Struktur der Liste ist bereits sichtbar, während die Daten
kommen. Kein Ladekreisel über der ganzen Seite.

Fehler: benennen, was nicht geklappt hat, und was zu tun ist. Keine
Entschuldigungen, keine Fehlercodes ohne Erklärung.

### Bewegung

Nur als Antwort auf eine Handlung. Der Übergang eines Termins in den
durchgestrichenen Zustand darf kurz animiert sein, weil er zeigt, was sich
geändert hat. Sonst nichts. `prefers-reduced-motion` wird respektiert.

### Qualitätsanforderungen

- bedienbar mit einer Hand auf dem iPhone, Schaltflächen mindestens 44 Punkt
- Hell- und Dunkelmodus über `prefers-color-scheme`, mit Farbtokens auf
  `:root`
- Tastaturbedienung mit sichtbarem Fokus
- kein Text unter 15 Punkt
- unter den Systemleisten des iPhones nichts abgeschnitten, also
  `viewport-fit=cover` und `env(safe-area-inset-*)` verwenden

### Vorgehen beim Bauen

Vor dem Schreiben des Codes einen kurzen Gestaltungsplan aufstellen: vier bis
sechs Farbwerte mit Namen, ein bis zwei Schriftfamilien mit ihren Rollen, ein
Layoutkonzept in zwei Sätzen. Diesen Plan gegen die Leitgedanken oben prüfen
und begründen, warum er zu dieser App passt und nicht zu jeder beliebigen.
Erst danach bauen.

### Anmeldung

Beim ersten Aufruf fragt die Seite nach einem Zugangsschlüssel. Dieser wird im
lokalen Speicher des Browsers abgelegt, gebunden an die Adresse der App. Er
wird niemals in eine Datei geschrieben oder an Dritte übertragen, sondern nur
im Kopf der Anfragen an die GitHub-Schnittstelle mitgeschickt.

Ein Knopf "Schlüssel entfernen" löscht ihn aus dem Browser.

Antwortet GitHub mit 401 oder 403, erklärt die App, dass der Schlüssel
abgelaufen oder ungültig ist, und fragt erneut danach.

### Die drei Bereiche

**Meine Termine**

Alle Termine der eigenen Teams aus `pool.json`, chronologisch, nach Datum
gruppiert. Jede Zeile mit Schalter zum Ausblenden.

**Andere Teams**

Dieselbe Darstellung für A-Jugend, 1. Herren und 1. Damen. Standardmäßig alles
aus. Einschalten übernimmt den Termin in den Extra-Feed. Oben eine Filterzeile
zum Eingrenzen auf ein Team.

**Eigener Termin**

Formular mit Titel, Datum, Startzeit, Endzeit, Ganztags-Schalter, Ort und
Notiz. Beim Ort eine Auswahlliste der bekannten Hallen aus `halls.yaml` plus
freie Eingabe.

Darunter die bereits angelegten eigenen Termine, jeweils mit Bearbeiten und
Löschen.

### Zeitraum

Standardmäßig nur Termine ab heute. Im Auswahlfeld zusätzlich: Letzte 30 Tage,
Letzte 12 Monate, Alle. Die Auswahl gilt für beide Listenbereiche.

### Speichern

Ein Knopf, beschriftet mit "Speichern und aktualisieren", der zwei Dinge tut:

1. `overrides.json` über die GitHub-Schnittstelle schreiben
2. den Workflow "Feeds aktualisieren" auslösen

Danach zeigt die App den Status des Laufs und meldet, wenn er fertig ist. Ein
Hinweis erklärt, dass die Feeds nach etwa einer Minute stehen und die
Kalender-Apps je nach Einstellung etwas später nachziehen.

Ungespeicherte Änderungen werden sichtbar markiert. Beim Verlassen der Seite
mit ungespeicherten Änderungen kommt eine Rückfrage.

### Konflikte

Vor dem Schreiben prüft die App, ob sich `overrides.json` seit dem Laden
geändert hat. Falls ja, wird gefragt, ob neu geladen oder überschrieben werden
soll. Das kann passieren, wenn die App auf zwei Geräten offen ist.

## 7. Workflow-Anpassungen

- `workflow_dispatch` muss aktiv sein, damit die App den Lauf auslösen kann
- der Lauf schreibt zusätzlich `docs/pool.json` und `docs/extra.ics`
- `overrides.json` wird gelesen, aber vom Workflow nie verändert
- schlägt das Lesen von `overrides.json` fehl, läuft der Rest trotzdem durch

## 8. Zugangsschlüssel

Ein eigener Fine-grained Token, getrennt vom Token für die Kommandozeile:

- Repository access: Only select repositories, dort `handball-kalender`
- Permissions: Contents auf Read and write, Actions auf Read and write
- Expiration: 90 Tage

Mehr Rechte braucht die App nicht. Bei Verlust oder Verdacht wird der Token auf
github.com gelöscht und ein neuer erstellt.

Die Adresse der Oberfläche ist
`https://alekspaunovic.github.io/handball-kalender/admin/`. Damit sie erreichbar
ist, muss GitHub Pages auf den Ordner `docs/` des Branches `main` zeigen.

Die Seite selbst ist öffentlich erreichbar, das lässt sich bei GitHub Pages
nicht verhindern. Ohne Schlüssel zeigt sie nur eine leere Liste und die
Aufforderung zur Anmeldung. Schreiben kann ohne ihn niemand.

## 9. Tests

- `overrides.json` fehlt: Feeds entstehen trotzdem, Warnung im Log
- `overrides.json` fehlerhaft: gleiches Verhalten
- UID in `hidden`: Termin fehlt im Feed, bleibt aber im Archiv
- UID aus `hidden` entfernt: Termin erscheint wieder
- Eintrag in `custom`: landet im Extra-Feed mit stabiler UID
- UID in `included`: Fremdspiel landet im Extra-Feed
- Freigeschaltetes Fremdspiel wird verlegt: Termin im Extra-Feed verschiebt
  sich, UID bleibt gleich
- Freigeschaltetes Fremdspiel wird zurückgezogen: ABGESAGT-Präfix
- `pool.json` enthält eigene und fremde Termine, korrekt über `own_team`
  unterschieden

## 10. Offene Punkte

Keine.
