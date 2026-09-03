# Projektregeln

## Geheime SpielerPlus-URLs

Die SpielerPlus-URLs (M2, M3, künftig MC) sind geheim. Sie stehen
ausschließlich in `.env` und in GitHub Secrets. Sie dürfen niemals in einer
anderen Datei auftauchen – auch nicht als Beispiel, Kommentar, Testdaten oder
in Log-Ausgaben. In Dokumentation und Code werden sie nur als Platzhalter wie
`aus GitHub Secret SPIELERPLUS_M2` referenziert.
