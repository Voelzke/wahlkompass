import { getElections } from "../lib/api";

export const revalidate = 60; // ISR: refresh every minute

export default async function StartPage() {
  const elections = await getElections();
  const active = elections.filter((e) => e.phase !== "archiv");

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-3 text-3xl font-bold text-gray-900">
        Welche Partei passt zu dir?
      </h1>
      <p className="mb-8 text-lg text-gray-600">
        Beantworte Thesen und vergleiche deine Positionen mit allen
        antretenden Parteien.
      </p>

      {active.length === 0 ? (
        <p className="rounded-lg bg-gray-100 px-4 py-3 text-gray-600">
          Aktuell ist keine Wahl aktiv.
        </p>
      ) : active.length === 1 ? (
        <a
          href={`/wahl/${active[0].id}`}
          className="inline-block rounded-xl bg-wk-green px-6 py-3 font-semibold text-white transition hover:bg-wk-green/90"
        >
          Zum Fragebogen — {active[0].title ?? active[0].region}
        </a>
      ) : (
        <div>
          <h2 className="mb-3 text-sm font-medium text-gray-500">
            Saison wählen
          </h2>
          <ul className="space-y-2">
            {active.map((e) => (
              <li key={e.id}>
                <a
                  href={`/wahl/${e.id}`}
                  className="block rounded-xl border border-gray-200 bg-white px-4 py-3 hover:border-gray-300"
                >
                  <span className="font-semibold text-gray-900">
                    {e.title ?? e.region}
                  </span>
                  <span className="ml-2 text-sm text-gray-500">{e.date}</span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
