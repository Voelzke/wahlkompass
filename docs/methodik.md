# Methodik — Wahlkompass

## Matching-Verfahren

Der Wahlkompass vergleicht Ihre Antworten zu einzelnen Thesen mit den Positionen der Parteien. Das Ergebnis zeigt, wie stark Ihre Positionen mit jeder Partei übereinstimmen.

### Berechnung im Detail

1. **Match-Wert pro These:** Für jede These wird berechnet, ob Sie und die Partei übereinstimmen.
   - Beide zustimmen **oder** beide ablehnen → Match = **+1** (Übereinstimmung)
   - Eine Seite zustimend, die andere ablehnend → Match = **−1** (Widerspruch)
   - Partei neutral / keine Aussage oder These übersprungen → Match = **0**

2. **Gewichtung:** Jede These hat ein Basisgewicht von 1. Mit der Funktion **„doppelte Gewichtung"** können Sie einer These doppeltes Gewicht geben (Faktor 2).

3. **Score:** `score(p) = Σ (match(p, t) × w(t))`

4. **Normierung:** `norm(p) = score(p) / Σ |w(t)|` über alle *beantworteten* (nicht übersprungenen) Thesen. So liegt das Ergebnis immer zwischen **−1** (volle Ablehnung) und **+1** (volle Übereinstimmung).

5. **Prozent:** `Prozent = (norm + 1) / 2 × 100` → **0 % bis 100 % Übereinstimmung**

6. **Mindestanzahl:** Es müssen mindestens **5 Thesen** beantwortet werden, sonst wird kein Ergebnis berechnet.

7. **Rangliste:** Parteien werden nach absteigender Übereinstimmung sortiert. Bei Gleichstand erhalten Parteien denselben Rang; die Reihenfolge innerhalb eines geteilten Rangs erfolgt alphabetisch nach Parteikürzel.

## Datenerfassung

Parteipositionen werden aus **Wahlprogrammen** und öffentlichen Stellungnahmen extrahiert. Jede Position ist mit einem **Beleg** (Zitat + Quelle) verknüpft und durchläuft einen Review-Prozess.

### Kategorien

Thesen sind in Kategorien eingeteilt (Wirtschaft, Soziales, Klima, Bildung, Migration, Europa, Innen, Demokratie, Verkehr, Digital). Sensible Kategorien (z. B. Migration, Innen) werden besonders sorgfältig geprüft.

## Review-Prozess

Alle extrahierten Positionen durchlaufen eine automatische und manuelle Validierung. Community-Korrekturen können über GitHub Issues eingereicht werden.

## KI-Transparenz

> ⚠️ **KI-Transparenzhinweis:** Bei der Extraktion von Positionen aus Wahlprogrammen kommen automatisierte Verfahren (LLM-basierte KI-Extraktion) zum Einsatz. Alle KI-generierten Positionen werden vor Veröffentlichung von einem Review-Prozess geprüft. KI-generierte Inhalte können Fehler enthalten — bitte verifizieren Sie wichtige Aussagen anhand der Originalquellen.

## Quellen & Lizenz

- **Code**: AGPL-3.0
- **Daten** (Parteien, Programme, Positionen): CC-BY-SA 4.0
- **Methodik & Dokumentation**: CC-BY-SA 4.0
