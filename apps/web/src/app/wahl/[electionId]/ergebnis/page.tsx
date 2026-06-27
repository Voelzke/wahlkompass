import { notFound } from "next/navigation";
import { getElectionData } from "../../../../lib/api";
import ResultsClient from "./ResultsClient";

export const revalidate = 60;

export default async function ResultsPage({
  params,
}: {
  params: { electionId: string };
}) {
  let data;
  try {
    data = await getElectionData(params.electionId);
  } catch {
    notFound();
  }

  const { election, parties, theses, positions } = data!;

  return (
    <ResultsClient
      electionId={params.electionId}
      election={election}
      parties={parties}
      theses={theses}
      positions={positions}
    />
  );
}
