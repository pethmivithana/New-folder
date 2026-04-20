import React from "react";
import RequirementTrackerModule from "../../components/features/sprint_impact_service/RequirementTrackerModule";
import Settings from "../../components/features/sprint_impact_service/Settings";

export default function ModulePage({ module }) {
  if (!module) return null;

  switch (module.id) {
    case "requirement-tracker":
      return <RequirementTrackerModule />; // loads backlog by default

    case "settings":
      return <Settings />;

    default:
      return null;
  }
}
