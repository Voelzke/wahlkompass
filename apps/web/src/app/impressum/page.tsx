export default function ImpressumPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-6 text-3xl font-bold text-gray-900">Impressum</h1>

      <div className="space-y-6 text-gray-700">
        <section>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Angaben gemäß § 5 TMG
          </h2>
          <p>
            Dieses Projekt wird von der Open-Source-Community betrieben.
            Für die Richtigkeit der erfassten Parteipositionen wird keine
            Gewähr übernommen.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Kontakt
          </h2>
          <p>
            Probleme, Korrekturen und Anfragen bitte über{" "}
            <a
              href="https://github.com/wahlkompass/wahlkompass/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              GitHub Issues
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Lizenz
          </h2>
          <ul className="ml-4 list-disc space-y-1">
            <li>Code: AGPL-3.0</li>
            <li>Daten (Parteien, Programme, Positionen): CC-BY-SA 4.0</li>
            <li>Methodik & Dokumentation: CC-BY-SA 4.0</li>
          </ul>
        </section>

        <section className="rounded-lg bg-amber-50 px-4 py-3 ring-1 ring-amber-200">
          <h2 className="mb-1 text-lg font-semibold text-amber-900">
            KI-Transparenzhinweis
          </h2>
          <p className="text-sm text-amber-800">
            Bei der Extraktion von Positionen aus Wahlprogrammen kommen
            automatisierte Verfahren (LLM-basierte KI-Extraktion) zum Einsatz.
            Alle KI-generierten Positionen werden vor Veröffentlichung von einem
            Review-Prozess geprüft. KI-generierte Inhalte können Fehler enthalten
            — bitte verifizieren Sie wichtige Aussagen anhand der
            Originalquellen.
          </p>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold text-gray-900">
            Haftungsausschluss
          </h2>
          <p className="text-sm">
            Der Wahlkompass ist ein neutraler Informationsdienst und keine
            Wahlwerbung. Die Darstellung der Positionen basiert auf öffentlichen
            Quellen. Parteien sind nicht für die Richtigkeit der hier
            wiedergegebenen Positionen verantwortlich.
          </p>
        </section>
      </div>
    </div>
  );
}
