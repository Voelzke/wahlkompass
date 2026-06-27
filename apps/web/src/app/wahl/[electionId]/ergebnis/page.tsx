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

  return (
    <ResultsClient
      electionId={params.electionId}
      election={data.election}
      parties={data.parties}
      theses={data.theses}
      positions={data.positions}
    />
  );
}
