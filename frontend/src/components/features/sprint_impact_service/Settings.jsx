import { useState, useEffect } from 'react';
import { Save, Info, AlertCircle, Settings as SettingsIcon, Loader2, Sparkles, Sliders, ShieldAlert, CheckCircle } from 'lucide-react';
import api from './api';

export default function Settings() {
  const [space, setSpace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    max_assignees: 5,
    focus_hours_per_day: 6.0,
    risk_appetite: 'Standard',
  });

  useEffect(() => {
    fetchSpace();
  }, []);

  const fetchSpace = async () => {
    try {
      setLoading(true);
      const spaces = await api.getSpaces();
      if (spaces && spaces.length > 0) {
        const currentSpace = spaces[0];
        setSpace(currentSpace);
        setFormData({
          name: currentSpace.name || '',
          description: currentSpace.description || '',
          max_assignees: currentSpace.max_assignees || 5,
          focus_hours_per_day: currentSpace.focus_hours_per_day || 6.0,
          risk_appetite: currentSpace.risk_appetite || 'Standard',
        });
      } else {
        setError("No space found. Please create a space first.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!space) return;
    try {
      setSaving(true);
      setError(null);
      await api.updateSpace(space.id, {
        name: formData.name,
        description: formData.description,
        max_assignees: parseInt(formData.max_assignees),
        focus_hours_per_day: parseFloat(formData.focus_hours_per_day),
        risk_appetite: formData.risk_appetite,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-red-50 border border-red-200 p-6 rounded-2xl max-w-md text-center shadow-lg">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Failed to load settings</h2>
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  const appetiteColors = {
    Strict: 'bg-rose-50 border-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.15)]',
    Standard: 'bg-indigo-50 border-indigo-200 shadow-[0_0_15px_rgba(99,102,241,0.15)]',
    Lenient: 'bg-emerald-50 border-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.15)]',
  };

  const appetiteDots = {
    Strict: 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]',
    Standard: 'bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]',
    Lenient: 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]',
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-100 blur-[120px]" />
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[40%] rounded-full bg-blue-100 blur-[100px]" />
      </div>

      <div className="max-w-4xl mx-auto relative z-10">
        {/* Header */}
        <div className="mb-12 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 bg-white rounded-2xl border border-gray-200 shadow-sm">
                <SettingsIcon className="w-8 h-8 text-indigo-600" />
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight text-gray-900">
                Space Configuration
              </h1>
            </div>
            <p className="text-gray-500 mt-2 text-lg">
              Fine-tune your agile workspace and AI risk thresholds.
            </p>
          </div>

          {/* Action Button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold transition-all duration-300 ${
              saveSuccess
                ? 'bg-emerald-50 text-emerald-600 border border-emerald-200 shadow-md'
                : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-md hover:shadow-lg'
            }`}
          >
            {saving ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : saveSuccess ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <Save className="w-5 h-5" />
            )}
            {saving ? 'Saving...' : saveSuccess ? 'Saved!' : 'Save Changes'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* General Information Card */}
          <div className="md:col-span-7 bg-white border border-gray-200 rounded-3xl p-8 shadow-xl relative group transition-all duration-500 hover:border-gray-300">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-transparent rounded-3xl pointer-events-none" />
            
            <div className="flex items-center gap-3 mb-8">
              <div className="p-2 bg-blue-50 rounded-lg border border-blue-100">
                <Info className="w-5 h-5 text-blue-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">General Information</h2>
            </div>

            <div className="space-y-6 relative z-10">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                  Space Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all placeholder-gray-400"
                  placeholder="e.g. Engineering Alpha"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                  Description
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  rows={3}
                  className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none placeholder-gray-400"
                  placeholder="Describe your team's mission..."
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                  Team Size (Max Assignees)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    name="max_assignees"
                    min="1"
                    max="50"
                    value={formData.max_assignees}
                    onChange={handleChange}
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <div className="w-16 text-center bg-gray-50 border border-gray-200 rounded-lg py-2 font-mono text-indigo-600 font-bold">
                    {formData.max_assignees}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI & Planning Tuning */}
          <div className="md:col-span-5 flex flex-col gap-8">
            
            {/* Risk Appetite */}
            <div className="bg-white border border-gray-200 rounded-3xl p-8 shadow-xl transition-all duration-500 hover:border-gray-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-amber-50 rounded-lg border border-amber-100">
                  <ShieldAlert className="w-5 h-5 text-amber-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">AI Risk Appetite</h2>
              </div>
              
              <p className="text-sm text-gray-500 mb-6">
                Adjusts how aggressive the AI decision engine is when suggesting deferrals or swaps based on predictions.
              </p>

              <div className="space-y-3">
                {['Strict', 'Standard', 'Lenient'].map((level) => (
                  <label
                    key={level}
                    className={`relative flex cursor-pointer rounded-xl border p-4 focus:outline-none transition-all duration-200 ${
                      formData.risk_appetite === level
                        ? appetiteColors[level]
                        : 'border-gray-200 bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <input
                      type="radio"
                      name="risk_appetite"
                      value={level}
                      checked={formData.risk_appetite === level}
                      onChange={handleChange}
                      className="sr-only"
                    />
                    <div className="flex w-full items-center justify-between">
                      <div className="flex items-center">
                        <div className="text-sm">
                          <p className={`font-bold text-gray-900`}>
                            {level}
                          </p>
                        </div>
                      </div>
                      {formData.risk_appetite === level && (
                        <div className={`w-3 h-3 rounded-full ${appetiteDots[level]}`} />
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Capacity Config */}
            <div className="bg-white border border-gray-200 rounded-3xl p-8 shadow-xl transition-all duration-500 hover:border-gray-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-emerald-50 rounded-lg border border-emerald-100">
                  <Sliders className="w-5 h-5 text-emerald-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">Capacity Tuning</h2>
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                    Focus Hours / Day
                  </label>
                  <span className="text-emerald-700 font-mono font-bold bg-emerald-50 border border-emerald-200 px-2 py-1 rounded">
                    {formData.focus_hours_per_day}h
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  Expected actual coding hours per developer, minus meetings and breaks.
                </p>
                <input
                  type="range"
                  name="focus_hours_per_day"
                  min="1"
                  max="12"
                  step="0.5"
                  value={formData.focus_hours_per_day}
                  onChange={handleChange}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
                />
              </div>
            </div>

          </div>
        </div>

        {/* AI Disclaimer */}
        <div className="mt-8 flex items-start gap-4 p-6 rounded-2xl bg-indigo-50 border border-indigo-100 shadow-sm">
          <Sparkles className="w-6 h-6 text-indigo-600 flex-shrink-0 mt-1" />
          <div>
            <h4 className="text-indigo-900 font-bold mb-1">Human-in-the-Loop Architecture</h4>
            <p className="text-sm text-indigo-800/80 leading-relaxed">
              These settings control the thresholds for the embedded machine learning pipelines (XGBoost & TabNet). 
              The system will provide automated recommendations based on your Risk Appetite, but the final decision to add, defer, or split a ticket always remains yours.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
