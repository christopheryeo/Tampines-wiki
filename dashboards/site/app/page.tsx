import type { Metadata } from "next";
import Dashboard from "./dashboard-client";

export const metadata: Metadata = {
  title: "Sentient.io Media Intelligence",
  description: "Deterministic media-monitoring intelligence from the SAF/MINDEF knowledge vault.",
};

export default function Home() {
  return <Dashboard />;
}
