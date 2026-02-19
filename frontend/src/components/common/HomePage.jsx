import React from 'react';
import { Heart, Users, FileText, MessageSquare, ChevronRight, Brain, TrendingUp, Shield } from 'lucide-react';

const HomePage = ({ setActiveModule }) => {
  const modules = [
    {
      id: 'emotion-monitoring',
      name: 'Emotion Monitoring',
      icon: Heart,
      developer: 'Fonseka A.A.T.N.',
      description: 'Real-time emotion detection and analysis of team members using facial expressions and sentiment analysis to track emotional states during Agile ceremonies.'
    },
    {
      id: 'expertise-recommendation',
      name: 'Expertise Recommendation',
      icon: Users,
      developer: 'Amarasinghe C.N.',
      description: 'Intelligent skill-matching system that recommends team members based on expertise, availability, and emotional readiness for optimal task allocation.'
    },
    {
      id: 'requirement-tracker',
      name: 'Requirement & Sprint Tracker',
      icon: FileText,
      developer: 'Vithana P.I',
      description: 'Comprehensive tracking of requirements and sprint progress with emotion-aware insights to monitor team sentiment and workload impact.'
    },
    {
      id: 'inclusive-communication',
      name: 'Inclusive Communication',
      icon: MessageSquare,
      developer: 'M.B.H. De Silva',
      description: 'Facilitate equitable communication channels that ensure all team members, including neurodiverse individuals, can effectively contribute and be heard.'
    },
  ];

  const systemCapabilities = [
    {
      icon: Brain,
      title: 'AI-Powered Emotion Detection',
      description: 'Continuously analyzes team emotional states to predict stress, frustration, and engagement levels.'
    },
    {
      icon: TrendingUp,
      title: 'Predictive Analytics',
      description: 'Forecasts emotional patterns and team dynamics to prevent burnout and improve team well-being.'
    },
    {
      icon: Shield,
      title: 'Inclusive Team Environment',
      description: 'Promotes psychological safety and ensures neurodiversity is valued in agile team collaboration.'
    },
  ];

  return (
    <div className="p-6 space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold text-gray-800">
          Welcome to AgileSense-AI
        </h1>
        <p className="text-gray-600 mt-2">
          Emotion-Aware Agile System for Enhanced Team Collaboration
        </p>
      </div>

      {/* System Overview */}
      <div className="bg-gradient-to-r from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">What AgileSense-AI Does</h2>
        <p className="text-gray-700 mb-4">
          AgileSense-AI is an emotion-aware system designed to enhance Agile team collaboration by integrating emotional intelligence into team workflows. It monitors team emotions, recommends optimal task assignments, tracks sprint progress with emotional context, and fosters inclusive communication.
        </p>
        <p className="text-gray-700">
          Our system helps teams identify emotional patterns, prevent burnout, improve decision-making, and create a psychologically safe environment where all team members, regardless of neurodiversity, can thrive.
        </p>
      </div>

      {/* Core Capabilities */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-gray-800">Core Capabilities</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {systemCapabilities.map((capability, index) => {
            const Icon = capability.icon;
            return (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
                <Icon className="text-blue-600 mb-2" size={24} />
                <h3 className="font-semibold text-gray-800 mb-2">{capability.title}</h3>
                <p className="text-sm text-gray-600">{capability.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modules */}
      <div>
        <h2 className="text-xl font-semibold mb-4 text-gray-800">System Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <div
                key={module.id}
                onClick={() => setActiveModule(module.id)}
                className="bg-white border-2 border-blue-100 rounded-lg p-6 hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Icon className="text-blue-600" size={28} />
                    <h2 className="text-lg font-semibold text-gray-800">
                      {module.name}
                    </h2>
                  </div>
                  <ChevronRight className="text-gray-400" />
                </div>

                <p className="text-sm text-gray-600 mb-3">
                  {module.description}
                </p>

                <p className="text-xs text-gray-500">
                  Developer: {module.developer}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default HomePage;
