import React from 'react';
import EmotionMonitoringHomePage from '../features/emotion_service/pages/EmotionMonitoringHomePage';
import ExpertiseRecommendationHomePage from '../features/expertise_service/pages/ExpertiseRecommendationHomePage';
import RequirementTrackerHomePage from '../features/sprint_impact_service/pages/RequirementTrackerHomePage';
import InclusiveCommunicationHomePage from '../features/communication_service/pages/InclusiveCommunicationHomePage';

const ModulePage = ({ module }) => {
  const renderModulePage = () => {
    switch (module.id) {
      case 'emotion-monitoring':
        return <EmotionMonitoringHomePage module={module} />;
      case 'expertise-recommendation':
        return <ExpertiseRecommendationHomePage module={module} />;
      case 'requirement-tracker':
        return <RequirementTrackerHomePage module={module} />;
      case 'inclusive-communication':
        return <InclusiveCommunicationHomePage module={module} />;
      default:
        return <div>Module not found</div>;
    }
  };

  return <>{renderModulePage()}</>;
};

export default ModulePage;