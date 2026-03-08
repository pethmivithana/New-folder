import { useState } from 'react';
import { Save, Info, AlertCircle, Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  // ═══════════════════════════════════════════════════════════════════════════
  // STATE: Configuration settings for AI, Rules, and General Agile settings
  // ═══════════════════════════════════════════════════════════════════════════

  // Tab 1: General (Standard Agile)
  const [sprintDuration, setSprintDuration] = useState('2');
  const [workingHoursPerDay, setWorkingHoursPerDay] = useState('8');
  const [velocityWindow, setVelocityWindow] = useState('last-3-sprints');

  // Tab 2: AI Tuning (Machine Learning)
  const [qualityRiskSensitivity, setQualityRiskSensitivity] = useState(40);
  const [sprintGoalStrictness, setSprintGoalStrictness] = useState(0.7);
  const [enableMLPredictions, setEnableMLPredictions] = useState(true);
  const [strictGibberishFilter, setStrictGibberishFilter] = useState(true);

  // Tab 3: Rule Engine (Decision Making)
  const [autoAnalyzeOnDragDrop, setAutoAnalyzeOnDragDrop] = useState(true);
  const [sprintBufferCapacity, setSprintBufferCapacity] = useState(15);
  const [defaultOverloadResolution, setDefaultOverloadResolution] = useState('prefer-swap');

  // Tab 4: Advanced
  const [modelFallbackBehavior, setModelFallbackBehavior] = useState('rule-based');

  // UI State
  const [activeTab, setActiveTab] = useState('general');
  const [saveStatus, setSaveStatus] = useState('');

  // ═══════════════════════════════════════════════════════════════════════════
  // EVENT HANDLERS
  // ═══════════════════════════════════════════════════════════════════════════

  const handleSaveConfiguration = async () => {
    const payload = {
      general: {
        sprintDuration: parseInt(sprintDuration),
        workingHoursPerDay: parseInt(workingHoursPerDay),
        velocityWindow,
      },
      aiTuning: {
        qualityRiskSensitivity,
        sprintGoalStrictness,
        enableMLPredictions,
        strictGibberishFilter,
      },
      ruleEngine: {
        autoAnalyzeOnDragDrop,
        sprintBufferCapacity,
        defaultOverloadResolution,
      },
      advanced: {
        modelFallbackBehavior,
      },
    };

    console.log('Configuration Payload:', JSON.stringify(payload, null, 2));
    setSaveStatus('Saved!');
    setTimeout(() => setSaveStatus(''), 2000);

    // TODO: Send to backend API
    // await api.saveConfiguration(payload);
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // UI COMPONENTS: Tab Navigation & Helper Components
  // ═══════════════════════════════════════════════════════════════════════════

  const TabButton = ({ id, label, isActive }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-4 py-2 font-medium transition-colors border-b-2 ${
        isActive
          ? 'border-indigo-600 text-indigo-600'
          : 'border-transparent text-gray-600 hover:text-gray-800'
      }`}
    >
      {label}
    </button>
  );

  const SettingRow = ({ label, description, children }) => (
    <div className="py-4 border-b border-gray-200 last:border-b-0">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-900">{label}</label>
          {description && <p className="mt-1 text-sm text-gray-600">{description}</p>}
        </div>
        <div className="ml-6 flex-shrink-0">{children}</div>
      </div>
    </div>
  );

  const HelpBox = ({ text }) => (
    <div className="mt-4 flex gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
      <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
      <p className="text-sm text-blue-700">{text}</p>
    </div>
  );

  const WarningBox = ({ text }) => (
    <div className="mt-4 flex gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
      <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
      <p className="text-sm text-amber-700">{text}</p>
    </div>
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // TAB 1: GENERAL (Standard Agile Settings)
  // ═══════════════════════════════════════════════════════════════════════════

  const GeneralTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Standard Agile Configuration</h3>

      <SettingRow
        label="Default Sprint Duration"
        description="How long each sprint typically lasts in your team."
      >
        <select
          value={sprintDuration}
          onChange={(e) => setSprintDuration(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="1">1 Week</option>
          <option value="2">2 Weeks</option>
          <option value="3">3 Weeks</option>
          <option value="4">4 Weeks</option>
        </select>
      </SettingRow>

      <SettingRow
        label="Working Hours per Day"
        description="Billable hours excluding meetings, admin, and breaks."
      >
        <input
          type="number"
          min="4"
          max="10"
          value={workingHoursPerDay}
          onChange={(e) => setWorkingHoursPerDay(e.target.value)}
          className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </SettingRow>
      <HelpBox text="Typical values: 6-8 hours for most teams. Account for meetings, Slack time, and admin tasks." />

      <SettingRow
        label="Velocity Calculation Window"
        description="How many past sprints to use for velocity averaging."
      >
        <select
          value={velocityWindow}
          onChange={(e) => setVelocityWindow(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="last-3-sprints">Last 3 Sprints</option>
          <option value="last-5-sprints">Last 5 Sprints</option>
          <option value="all-time">All-time Average</option>
        </select>
      </SettingRow>
      <HelpBox text="Use 3-5 sprints for stable teams. Use all-time for long-running projects to capture trends." />
    </div>
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // TAB 2: AI TUNING (Machine Learning Configuration)
  // ═══════════════════════════════════════════════════════════════════════════

  const AITuningTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Machine Learning & AI Tuning</h3>
      <p className="text-sm text-gray-600">Fine-tune the ML models to match your team's culture and risk tolerance.</p>

      <SettingRow
        label="Quality Risk Sensitivity"
        description="Alert threshold for defect probability. Lower = more strict."
      >
        <div className="w-48">
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0"
              max="100"
              value={qualityRiskSensitivity}
              onChange={(e) => setQualityRiskSensitivity(parseInt(e.target.value))}
              className="w-full accent-indigo-600"
            />
            <span className="text-sm font-medium text-gray-900 w-12">{qualityRiskSensitivity}%</span>
          </div>
        </div>
      </SettingRow>
      <HelpBox text={`Alert me if quality defect probability exceeds ${qualityRiskSensitivity}%. Lower values = stricter quality gates.`} />

      <SettingRow
        label="Sprint Goal Strictness"
        description="TF-IDF cosine similarity threshold for sprint goal alignment."
      >
        <div className="w-48">
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={sprintGoalStrictness}
              onChange={(e) => setSprintGoalStrictness(parseFloat(e.target.value))}
              className="w-full accent-indigo-600"
            />
            <span className="text-sm font-medium text-gray-900 w-12">{sprintGoalStrictness.toFixed(1)}</span>
          </div>
        </div>
      </SettingRow>
      <HelpBox text={`Current threshold: ${sprintGoalStrictness}. Items below this similarity score are flagged as off-goal.`} />

      <div className="border-t border-gray-200 pt-6">
        <SettingRow
          label="Enable ML Predictions"
          description="Use machine learning models for effort, schedule, and quality predictions."
        >
          <button
            onClick={() => setEnableMLPredictions(!enableMLPredictions)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              enableMLPredictions ? 'bg-indigo-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                enableMLPredictions ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </SettingRow>
      </div>

      {enableMLPredictions && <HelpBox text="XGBoost models are active for effort/schedule. PyTorch TabNet is active for quality risk." />}

      <SettingRow
        label="Strict Agile Formatting & Gibberish Filter"
        description="Reject tickets with keyboard smash, poor descriptions, or invalid format."
      >
        <button
          onClick={() => setStrictGibberishFilter(!strictGibberishFilter)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            strictGibberishFilter ? 'bg-indigo-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              strictGibberishFilter ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </SettingRow>
      <WarningBox text="When enabled, inputs like 'asdfghjkl' or 'aaaa bbb' will be rejected. Helps save server resources." />
    </div>
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // TAB 3: RULE ENGINE (Decision Making Rules)
  // ═══════════════════════════════════════════════════════════════════════════

  const RuleEngineTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Rule Engine & Decision Making</h3>
      <p className="text-sm text-gray-600">Configure how the system makes automatic sprint planning decisions.</p>

      <SettingRow
        label="Auto-Analyze on Drag-and-Drop"
        description="Automatically run impact analysis when items are moved between sprints or statuses."
      >
        <button
          onClick={() => setAutoAnalyzeOnDragDrop(!autoAnalyzeOnDragDrop)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            autoAnalyzeOnDragDrop ? 'bg-indigo-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              autoAnalyzeOnDragDrop ? 'translate-x-6' : 'translate-x-1'
            }`}
          />
        </button>
      </SettingRow>
      <HelpBox text="Disable for performance on large sprints. Re-enable for real-time decision support." />

      <SettingRow
        label="Sprint Buffer Capacity"
        description="Percentage of sprint capacity to keep free for emergencies and unplanned work."
      >
        <div className="flex items-center gap-2">
          <input
            type="number"
            min="0"
            max="50"
            value={sprintBufferCapacity}
            onChange={(e) => setSprintBufferCapacity(parseInt(e.target.value))}
            className="w-20 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <span className="text-sm text-gray-600">%</span>
        </div>
      </SettingRow>
      <HelpBox text={`Example: 30 SP sprint with 15% buffer = 25.5 SP for planned items, 4.5 SP reserved.`} />

      <SettingRow
        label="Default Overload Resolution Strategy"
        description="When sprint capacity is exceeded, which mitigation strategy to suggest first."
      >
        <select
          value={defaultOverloadResolution}
          onChange={(e) => setDefaultOverloadResolution(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="prefer-swap">Prefer Swap (replace low-value items)</option>
          <option value="prefer-split">Prefer Split (break into smaller pieces)</option>
          <option value="prefer-defer">Prefer Defer (move to next sprint)</option>
        </select>
      </SettingRow>
      <HelpBox text="This is the initial suggestion. PMs can always override and explore other options." />
    </div>
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // TAB 4: ADVANCED (Expert Settings)
  // ═══════════════════════════════════════════════════════════════════════════

  const AdvancedTab = () => (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">Advanced Configuration</h3>
      <p className="text-sm text-gray-600">Expert-level settings. Only modify if you understand the implications.</p>

      <WarningBox text="Advanced settings can significantly impact system behavior. Changes are logged for audit purposes." />

      <SettingRow
        label="Model Fallback Behavior"
        description="What to do if an ML model fails or returns invalid predictions."
      >
        <select
          value={modelFallbackBehavior}
          onChange={(e) => setModelFallbackBehavior(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="rule-based">Use Rule-Based Math Fallback</option>
          <option value="show-error">Show Error to User</option>
          <option value="use-last-valid">Use Last Valid Prediction</option>
        </select>
      </SettingRow>
      <HelpBox text="Rule-Based Math: Uses velocity + effort sizing. Recommended for production environments." />
      <HelpBox text="Show Error: Alerts user. Requires manual decision. Use for testing/debugging." />
    </div>
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // MAIN RENDER
  // ═══════════════════════════════════════════════════════════════════════════

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <SettingsIcon className="w-8 h-8 text-indigo-600" />
            <h1 className="text-3xl font-bold text-gray-900">AI & Risk Configuration</h1>
          </div>
          <p className="text-gray-600 max-w-2xl">
            Configure your Agile Replanning system to match your team's culture, risk tolerance, and decision-making preferences. This is a Human-in-the-Loop AI system—you're in control.
          </p>
        </div>

        {/* Main Settings Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {/* Tabs Navigation */}
          <div className="border-b border-gray-200 px-6">
            <div className="flex gap-1">
              <TabButton id="general" label="General" isActive={activeTab === 'general'} />
              <TabButton id="ai-tuning" label="AI Tuning" isActive={activeTab === 'ai-tuning'} />
              <TabButton id="rule-engine" label="Rule Engine" isActive={activeTab === 'rule-engine'} />
              <TabButton id="advanced" label="Advanced" isActive={activeTab === 'advanced'} />
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'general' && <GeneralTab />}
            {activeTab === 'ai-tuning' && <AITuningTab />}
            {activeTab === 'rule-engine' && <RuleEngineTab />}
            {activeTab === 'advanced' && <AdvancedTab />}
          </div>
        </div>

        {/* Save Button & Status */}
        <div className="mt-8 flex items-center justify-between">
          <button
            onClick={handleSaveConfiguration}
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors shadow-sm"
          >
            <Save className="w-5 h-5" />
            Save Configuration
          </button>

          {saveStatus && (
            <div className="text-sm font-medium text-green-600 animate-pulse">
              ✓ {saveStatus}
            </div>
          )}
        </div>

        {/* Footer Info */}
        <div className="mt-12 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">
            <strong>Human-in-the-Loop Design:</strong> These settings empower you to tune the AI to your team's specific needs. The system learns from your decisions and provides recommendations, but you always decide.
          </p>
        </div>
      </div>
    </div>
  );
}
