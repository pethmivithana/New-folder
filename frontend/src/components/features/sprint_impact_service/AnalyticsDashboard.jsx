export default function AnalyticsDashboard({ space }) {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Analytics & Charts</h2>
        <div className="grid grid-cols-2 gap-6">
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">📈 Burndown Chart</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">Install recharts: npm install recharts</p>
            </div>
          </div>
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">⚡ Velocity Chart</h3>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
              <p className="text-gray-500">Chart coming soon</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Analysis History</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50">
              <tr>
                <th className="px-6 py-3">Date</th>
                <th className="px-6 py-3">Item</th>
                <th className="px-6 py-3">Sprint</th>
                <th className="px-6 py-3">Risk</th>
                <th className="px-6 py-3">Recommendation</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                  No history yet
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}