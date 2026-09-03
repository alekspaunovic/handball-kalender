# Handball-Kalender-Feeds TB Wülfrath

Spezifikation für ein Skript, das aus SpielerPlus- und handball.net-Feeds
sechs eigene ICS-Kalender erzeugt und per GitHub Pages veröffentlicht.

## 1. Ziel

Ein Nutzer spielt in der 2. und 3. Herren des TB Wülfrath und trainiert die
männliche C-Jugend. Trainings kommen aus SpielerPlus, Spiele aus handball.net.
Beide Quellformate gefallen ihm nicht. Das Skript liest die Quell-Feeds,
schreibt die Termine in ein festes Wunschformat um und veröffentlicht sie als
statische ICS-Dateien, die im Apple-Kalender abonniert werden.

Wichtig: Es werden keine Termine in einen Kalender geschrieben. Das Skript
erzeugt ausschließlich Dateien. Der Nutzer abonniert die URLs.

## 2. Quellen

### SpielerPlus (Trainings und sonstige Termine)

| Team | URL |
| --- | --- |
| M2 | aus GitHub Secret SPIELERPLUS_M2 |
| M3 | aus GitHub Secret SPIELERPLUS_M3 |
| MC | noch nicht vorhanden, wird nachgereicht |

Diese URLs sind personalisierte Geheim-Links. Sie gehören in GitHub Secrets,
nicht ins Repository.

### handball.net (Spiele)

| Team | URL |
| --- | --- |
| M2 | https://www.handball.net/kalender/team/74503.ics |
| M3 | https://www.handball.net/kalender/team/75902.ics |
| MC | https://www.handball.net/kalender/team/95749.ics |

Diese URLs sind öffentlich und können in der Konfiguration stehen.

### Abgrenzung der Quellen

Die SpielerPlus-Feeds enthalten auch Spiele. Diese werden ignoriert, weil die
Spieldaten aus handball.net gezogen werden. Die Unterscheidung erfolgt über das
UID-Präfix, das SpielerPlus vergibt:

- `training.<id>` wird übernommen
- `event.<id>` wird übernommen
- alles andere (insbesondere Spiel-UIDs) wird verworfen

Bei unbekannten Präfixen: übernehmen und im Log als Warnung ausgeben, damit
nichts stillschweigend verlorengeht.

## 3. Ausgabe

Sechs Feeds, getrennt nach Team und Typ:

| Datei | Inhalt | Quelle |
| --- | --- | --- |
| `m2-training.ics` | Trainings und sonstige Termine 2. Herren | SpielerPlus M2 |
| `m2-spiele.ics` | Spiele 2. Herren | handball.net 74503 |
| `m3-training.ics` | Trainings und sonstige Termine 3. Herren | SpielerPlus M3 |
| `m3-spiele.ics` | Spiele 3. Herren | handball.net 75902 |
| `mc-training.ics` | Trainings und sonstige Termine C-Jugend | SpielerPlus MC |
| `mc-spiele.ics` | Spiele C-Jugend | handball.net 95749 |

Solange der MC-SpielerPlus-Link fehlt, wird `mc-training.ics` nicht erzeugt.
Das Skript darf deswegen nicht abbrechen.

Kalender-Header je Datei:

```
X-WR-CALNAME:TBW 2. Herren Training      (analog für die anderen)
X-WR-TIMEZONE:Europe/Berlin
X-PUBLISHED-TTL:PT6H
REFRESH-INTERVAL;VALUE=DURATION:PT6H
```

Es werden keine VALARM-Komponenten erzeugt. Keine Wegzeit, keine Erinnerungen.
Der Nutzer setzt sich das bei Bedarf selbst.

## 4. Team-Konfiguration

| Kürzel | Anzeigename | Eigenname bei handball.net | Treffpunkt Spiel | Treffpunkt Training | Spieldauer |
| --- | --- | --- | --- | --- | --- |
| M2 | 2. Herren | TB Wülfrath II | 1:15 h vorher | 10 min vorher | 1:30 h |
| M3 | 3. Herren | TB Wülfrath III | 1:00 h vorher | keiner | 1:30 h |
| MC | C-Jugend | TB Wülfrath | 1:00 h vorher | keiner | 1:15 h |

Der Eigenname wird aus dem `X-WR-CALNAME` des jeweiligen handball.net-Feeds
gelesen, nicht hart kodiert. Vergleich immer case-insensitiv und ohne
Mehrfach-Leerzeichen, weil die Schreibweise zwischen den Feeds schwankt
(`TB WÜLFRATH III` vs. `TB Wülfrath II`).

## 5. Transformation Trainings (SpielerPlus)

### Titel

Grundform: `Training <Anzeigename>`

Beispiel: `Training 3. Herren`

Der SpielerPlus-Titel hat das Muster `Training - <Ortszusatz>` oder nur
`Training`. Ist ein Ortszusatz vorhanden, wird er angehängt:

`Training - Erbacher Berg` wird zu `Training 3. Herren - Erbacher Berg`

Termine, deren Titel nicht mit `Training` beginnt (Beispiele aus den Rohdaten:
`Teamevent`, `Auftakt zur Vorbereitung`), bekommen die Form
`<Anzeigename>: <Originaltitel>`, also `2. Herren: Teamevent`.

### Zeiten

Start und Ende werden unverändert aus der Quelle übernommen, inklusive
`TZID=Europe/Berlin`. Auch dann, wenn die Quelle einen längeren Hallenblock
liefert als die tatsächliche Trainingszeit. Das ist so gewollt.

### Ort

Die M3-Termine haben kein LOCATION-Feld, der Ort steckt nur im Titelzusatz.
Die M2-Termine haben LOCATION plus GEO plus
`X-APPLE-STRUCTURED-LOCATION`. Eine vorhandene LOCATION ist die
verlässlichste Information und darf nicht durch die Standardhalle Fliethe
ersetzt werden. Regel in dieser Reihenfolge:

1. Quelle liefert LOCATION: diese verwenden, zusammen mit GEO und
   `X-APPLE-STRUCTURED-LOCATION`, falls vorhanden. Entspricht die Adresse
   einer Halle aus der Hallentabelle (Abschnitt 8), stattdessen den Eintrag
   aus der Hallentabelle nehmen, damit die Schreibweise einheitlich bleibt.
2. Keine LOCATION, aber ein Ortszusatz im Titel, der in der Hallentabelle
   bekannt ist: Adresse aus der Tabelle
3. Keine LOCATION und kein Ortszusatz im Titel: Standardhalle Fliethe
4. Keine LOCATION und ein unbekannter Ortszusatz im Titel: Ortszusatz als
   reinen Text setzen und im Log warnen

In den Fällen, in denen die Adresse aus der Hallentabelle kommt (Fall 1 bei
Treffer, Fall 2, Fall 3), wird sie als vollständiger String geschrieben:

```
LOCATION:Sporthalle Fliethe\, Fortunastraße 30\, 42489 Wülfrath\, Deutschland
```

Zusätzlich `GEO` und `X-APPLE-STRUCTURED-LOCATION` aus der Hallentabelle
setzen, damit Apple die Navigation direkt anbietet.

### Notizen

- M2-Training: `Treffpunkt: HH:MM` mit Beginn minus 10 Minuten
- M3 und MC: keine Notiz
- sonstige Termine (Teamevent etc.): keine Notiz

Die Quell-DESCRIPTION enthält nur den SpielerPlus-Link und wird verworfen.

## 6. Transformation Spiele (handball.net)

### Heim oder Auswärts

Bestimmt über die Halle, nicht über die Spielplanseite. Liegt das Spiel in der
Heimhalle (Fliethe, bei handball.net `MTC ARENA WÜLFRATH`, Fortunastraße 30),
gilt es als Heimspiel, sonst als Auswärtsspiel.

Grund: Am 19.09. hat die MC vier Spiele in der Voss-Arena Wippperfürth, bei
zweien steht TB Wülfrath auf der Heimseite. Das ist ein Turnier, faktisch also
auswärts. Nach Halle bestimmt liefert das richtige Ergebnis.

Hat ein Spiel gar kein LOCATION-Feld, wird `Auswärts` angenommen und geloggt.

### Gegner

Die SUMMARY hat die Form `<Heim> - <Gast>`, teilweise mit angehängtem Ergebnis
in Klammern. Vorgehen:

1. Ergebnis in Klammern am Ende abtrennen und merken
2. An ` - ` splitten
3. Die Seite, die dem Eigennamen des Teams entspricht, ist man selbst
4. Die andere Seite ist der Gegner

Achtung: Bei `TB WÜLFRATH III - TB WÜLFRATH IV` stehen auf beiden Seiten
TB Wülfrath. Der Vergleich muss deshalb auf den vollständigen Seitenstring
gehen, nicht auf ein Teilstring-Enthaltensein.

### Gegnername normalisieren

handball.net liefert Namen in Großbuchstaben und mit Zusätzen. Ziel ist die
Schreibweise aus dem Wunschformat, also `Lüttringhauser TV`.

Regeln:

1. Mojibake reparieren, siehe Abschnitt 9
2. Ist der Name bereits gemischt geschrieben, unverändert lassen
3. Ist er komplett groß, in Title Case wandeln, dabei bekannte Abkürzungen
   groß lassen: TV, TB, TSV, TuS, TUS, HV, HC, SV, SG, JSG, HSV, SSG, DJK,
   MTG, MTV, VfL, VfB, HG, HSG, SC, FC, TG
4. Angehängte Mannschaftskennungen wie `1M`, `2.M`, `2.Herren` entfernen
5. Römische Zahlen am Ende (II, III, IV) beibehalten
6. Mehrfache Leerzeichen zusammenfassen

Beispiele:

| Quelle | Ergebnis |
| --- | --- |
| `Lüttringhauser TV` | `Lüttringhauser TV` |
| `NEUSSER HV 1M` | `Neusser HV` |
| `DJK GRÜN WEISS WERDEN 2.M` | `DJK Grün Weiss Werden` |
| `SSG WUPPERTAL/HSV WUPPERTAL` | `SSG Wuppertal/HSV Wuppertal` |
| `TB WÜLFRATH IV` | `TB Wülfrath IV` |
| `TUS LINTFORT` | `TuS Lintfort` |
| `MTG Horst Essen` | `MTG Horst Essen` |

Eine Override-Tabelle in der Konfiguration erlaubt es, Einzelfälle von Hand zu
korrigieren. Sie wird vor allen Regeln geprüft.

### Titel

`<Anzeigename> <Heim|Auswärts> <Gegner>`

Beispiel: `2. Herren Heim Lüttringhauser TV`

Bei Absage wird `ABGESAGT ` vorangestellt:
`ABGESAGT 2. Herren Heim Lüttringhauser TV`

### Zeiten

Startzeit ist die Anwurfzeit aus der Quelle. Die Endzeit von handball.net ist
immer Start plus zwei Stunden und damit nicht brauchbar. Sie wird durch die
Spieldauer aus der Team-Konfiguration ersetzt, also Herren 1:30 h und Jugend
1:15 h.

Spiele ohne Anwurfzeit kommen als Ganztagestermin
(`DTSTART;VALUE=DATE`). Diese bleiben Ganztagestermine, bekommen keine
Treffpunkt-Notiz, sondern die Notiz `Uhrzeit noch offen`.

### Ort

Adresse aus der Hallentabelle, falls die Halle bekannt ist. Sonst generische
Bereinigung nach Abschnitt 9. Immer als vollständiger String mit
`, Deutschland` am Ende.

Für Heimspiele wird die Halle immer als `Sporthalle Fliethe` ausgegeben, nie
als `MTC Arena Wülfrath`.

### Notizen

Zeile 1: `Treffpunkt: HH:MM` (Anwurf minus Vorlauf laut Team-Konfiguration).
Bei Auswärtsspielen ist der Treffpunkt an der Gasthalle, es braucht deshalb
keinen Zusatztext.

Zeile 2, nur wenn ein Ergebnis in der SUMMARY stand: `Ergebnis: 34:25`

Ganztagestermine bekommen statt Zeile 1 die Zeile `Uhrzeit noch offen`.

Die restliche Quell-DESCRIPTION (Liga, Spieltag, Spielnummer, Status, Link)
wird verworfen. Der Link wandert in das URL-Feld.

## 7. Absagen und Verlegungen

handball.net führt in der DESCRIPTION ein Statuswort:

| Wort | Bedeutung | Verhalten |
| --- | --- | --- |
| `Pendiente` | ausstehend | normal |
| `Finalizado` | gespielt | normal, Ergebnis in die Notiz |
| `Retirado` | zurückgezogen | sofort als abgesagt markieren |

Weitere unbekannte Statuswörter: als normal behandeln und loggen.

Zusätzlich die Verschwinden-Logik: Ist ein Spiel im Archiv, taucht aber nicht
mehr in der Quelle auf, bleibt es zunächst unverändert stehen. Erst wenn sein
Termin vorbei ist und es weiterhin fehlt, bekommt es das ABGESAGT-Präfix. So
werden Verlegungen nicht fälschlich als Absage markiert.

Ändern sich Zeit oder Ort eines bekannten Spiels, wird der Archiveintrag
aktualisiert. Die UID bleibt dabei stabil, damit der Apple-Kalender den Termin
verschiebt statt einen zweiten anzulegen.

## 8. Hallentabelle

Konfigurationsdatei `halls.yaml`. Schlüssel sind normalisierte Suchbegriffe
(kleingeschrieben, ohne Sonderzeichen), Werte enthalten Anzeigename, Adresse
und Koordinaten.

Bekannt:

| Suchbegriff | Anzeigename | Adresse | Koordinaten |
| --- | --- | --- | --- |
| fliethe, mtc arena wülfrath | Sporthalle Fliethe | Fortunastraße 30, 42489 Wülfrath | 51.2820, 7.0398 (prüfen) |
| flehenberg | Sporthalle Flehenberg | Flehenberg 91, 42489 Wülfrath | noch ermitteln |
| frankys gym, franky's gym | Franky's Gym | Glockenstahlstraße 1, 42857 Remscheid (PLZ prüfen) | noch ermitteln |
| erbacher berg | Sportplatz Erbacher Berg (1. FC) | Silberberger Weg 3, Innenstadt, 42489 Wülfrath | noch ermitteln |

Alle Adressen enden im ICS mit `, Deutschland`.

Unbekannte Hallen werden nicht geraten, sondern generisch bereinigt und
geloggt, damit die Tabelle nach und nach wachsen kann.

## 9. Bereinigung von handball.net-Adressen

Die Quelle liefert kaputte Strings:

```
MTC ARENA WüLFRATH\, FORTUNA STR. 30\, 42489 WüLFRATH\, 42489 WüLFRATH
BOCKMüHLE\, MERCATORSTR.\, 45143 ESSEN\, 45143 ESSEN
MATARé-GYMNASIUM\, NIEDERDONKER STR. 34\, 40667 MEERBUSCH\, 40667 MEERBUSCH
```

Probleme und Behandlung:

1. Halb-großgeschriebene Umlaute (`WüLFRATH`, `MATARé`). Das Skript muss
   sowohl diese Variante als auch korrekt kodierte Umlaute verarbeiten. Nach
   der Title-Case-Wandlung ist das Problem gelöst.
2. Doppelte PLZ und Stadt am Ende. Das letzte Komma-Segment entfernen, wenn es
   im vorletzten Segment bereits enthalten ist.
3. Alles in Title Case wandeln, Straßenabkürzungen normalisieren
   (`STR.` zu `Str.`).
4. `, Deutschland` anhängen.

Ergebnis für die Beispiele:

```
Bockmühle, Mercatorstr., 45143 Essen, Deutschland
Mataré-Gymnasium, Niederdonker Str. 34, 40667 Meerbusch, Deutschland
```

## 10. Archiv

Termine sollen dauerhaft im Kalender bleiben. Die Quellen liefern nur ein
rollierendes Fenster. Deshalb führt das Skript pro Feed eine JSON-Datei unter
`data/<feed>.json`, die bei jedem Lauf ergänzt und ins Repository
zurückcommittet wird.

Struktur je Eintrag:

```json
{
  "uid": "tbw-m2-spiel-380455",
  "source_uid": "spiel-380455@mmcc-news",
  "summary": "2. Herren Heim Lüttringhauser TV",
  "dtstart": "2026-09-19T15:50:00+02:00",
  "dtend": "2026-09-19T17:20:00+02:00",
  "all_day": false,
  "location": "Sporthalle Fliethe, Fortunastraße 30, 42489 Wülfrath, Deutschland",
  "geo": [51.282, 7.0398],
  "description": "Treffpunkt: 14:35",
  "url": "https://www.handball.net/match/380455",
  "cancelled": false,
  "first_seen": "2026-09-02T09:00:00Z",
  "last_seen": "2026-09-02T09:00:00Z"
}
```

Der Feed wird immer vollständig aus dem Archiv erzeugt, nicht aus der Quelle.
Die Quelle aktualisiert nur das Archiv.

UIDs werden aus einem festen Präfix und der Quell-ID gebildet und ändern sich
nie. Beispiel: `tbw-m2-spiel-380455`, `tbw-m3-training-77001458`.

## 11. Technik

- Python 3.12, Abhängigkeiten `icalendar` und `requests`
- Konfiguration in `config.yaml`, Hallen in `halls.yaml`
- SpielerPlus-URLs aus GitHub Secrets, per Umgebungsvariable ins Skript
- GitHub Actions, Cron alle 6 Stunden plus manueller Trigger
- Ausgabe nach `docs/`, Veröffentlichung über GitHub Pages
- Der Workflow committet `docs/*.ics` und `data/*.json` zurück
- Bei Fehlern einer einzelnen Quelle laufen die übrigen Feeds weiter; das
  Archiv des fehlgeschlagenen Feeds bleibt unverändert und der bestehende
  Feed wird unverändert neu geschrieben
- Zeitzone durchgehend Europe/Berlin, VTIMEZONE korrekt einbetten

## 12. Tests

Die in dieser Spezifikation zitierten Rohdaten dienen als Fixtures. Mindestens
abzudecken:

- M3-Training ohne Ortszusatz wird Fliethe
- M3-Training mit Ortszusatz Erbacher Berg wird korrekt aufgelöst
- M2-Training erzeugt Treffpunkt-Notiz mit Beginn minus 10 Minuten
- M2-Spiel gegen Lüttringhauser TV ergibt exakt den Titel aus dem Wunschformat
- MC-Turnierspiel am 19.09. mit TB Wülfrath auf der Heimseite wird `Auswärts`
- `TB WÜLFRATH III - TB WÜLFRATH IV` erkennt den richtigen Gegner
- `Retirado` erzeugt das ABGESAGT-Präfix
- Ganztagesspiel bekommt keine Treffpunkt-Notiz
- Spiel mit Ergebnis in der SUMMARY: Ergebnis wandert in die Notiz
- Verschwundenes Spiel vor dem Termin bleibt unverändert, nach dem Termin wird
  es als abgesagt markiert
- Adressbereinigung für alle drei Beispielstrings aus Abschnitt 9

## 13. Offene Punkte

- Postleitzahl Franky's Gym Remscheid bestätigen
- Koordinaten für alle vier Hallen ermitteln (kann das Skript beim ersten Lauf
  einmalig per Geocoding tun, Ergebnis dann fest in halls.yaml eintragen)
- SpielerPlus-Link der C-Jugend
- Prüfen, ob die MC-Spiele in der Voss-Arena tatsächlich ein Turnier sind
