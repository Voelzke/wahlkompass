import { notFound } from "next/navigation";
import { getElectionData } from "../../../../lib/api";
import MatchingFlow from "./MatchingFlow";

export const revalidate = 60;

export default async function MatchingPage({
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
    <MatchingFlow
      electionId={params.electionId}
      electionTitle={data.election.title ?? data.election.region}
      theses={data.theses}
      categories={data.categories}
    />
  );
}
