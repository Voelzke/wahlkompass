import { getMethodik } from "../../lib/api";
import MethodikContent from "./MethodikContent";

export const revalidate = 3600;

export default async function MethodikPage() {
  const markdown = await getMethodik();
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <MethodikContent markdown={markdown} />
    </div>
  );
}
