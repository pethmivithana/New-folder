import React from "react";
import RequirementTrackerModule from "../../components/features/sprint_impact_service/RequirementTrackerModule";

export default function ModulePage({ module }) {
  if (!module) return null;

  switch (module.id) {
    case "requirement-tracker":
      return <RequirementTrackerModule />; // loads backlog by default

    case "emotion-monitoring":
      return (
        <div className="p-6">
          <h2 className="text-2xl font-bold">Emotion Monitoring</h2>
          <p className="text-gray-600">Module under development</p>
        </div>
      );

    case "expertise-recommendation":
      return (
        <div className="p-6">
          <h2 className="text-2xl font-bold">Expertise Recommendation</h2>
          <p className="text-gray-600">Module under development</p>
        </div>
      );

    case "inclusive-communication":
      return (
        <div className="p-6">
          <h2 className="text-2xl font-bold">Inclusive Communication</h2>
          <p className="text-gray-600">Module under development</p>
        </div>
      );

    default:
      return null;
  }
}
