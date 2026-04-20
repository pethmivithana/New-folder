import React from "react";
import RequirementTrackerModule from "../../components/features/sprint_impact_service/RequirementTrackerModule";

export default function ModulePage({ module }) {
  if (!module) return null;

  switch (module.id) {
    case "requirement-tracker":
      return <RequirementTrackerModule />; // loads backlog by default

    default:
      return null;
  }
}
