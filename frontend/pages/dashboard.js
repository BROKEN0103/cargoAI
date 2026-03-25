import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDashboardStats } from '../services/api';
import { ShieldAlert, Fingerprint, Activity } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats().then(data => {
      setStats(data);
      setLoading(false);
    }).catch(console.error);
  }, []);

  if (loading) return <div className="text-gray-400 animate-pulse">Loading intelligence feed...</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Command Center</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
          <div className="flex items-center gap-4 text-blue-400 mb-2">
            <Activity size={24} />
            <h2 className="text-sm font-semibold uppercase tracking-wider">Total Scans</h2>
          </div>
          <p className="text-4xl font-black text-white">{stats.total_scans}</p>
        </div>

        <div className="bg-red-900/20 p-6 rounded-xl border border-red-500/30 shadow-lg">
          <div className="flex items-center gap-4 text-red-500 mb-2">
            <ShieldAlert size={24} />
            <h2 className="text-sm font-semibold uppercase tracking-wider">High Risk Alerts</h2>
          </div>
          <p className="text-4xl font-black text-red-500">{stats.high_risk_scans}</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
          <div className="flex items-center gap-4 text-gray-400 mb-2">
            <Fingerprint size={24} />
            <h2 className="text-sm font-semibold uppercase tracking-wider">System Status</h2>
          </div>
          <p className="text-xl font-medium text-green-400 mt-2">SECURE & ONLINE</p>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">Recent Activity</h2>
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden shadow-lg">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-900/50 text-gray-400 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium border-b border-gray-700">Scan ID</th>
                <th className="p-4 font-medium border-b border-gray-700">Date</th>
                <th className="p-4 font-medium border-b border-gray-700">Risk Score</th>
                <th className="p-4 font-medium border-b border-gray-700">Risk Level</th>
                <th className="p-4 font-medium border-b border-gray-700 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {stats.recent_activity.map(scan => (
                <tr key={scan.id} className="hover:bg-gray-750 transition-colors">
                  <td className="p-4 font-mono text-sm">#{scan.id}</td>
                  <td className="p-4 text-gray-400">{new Date(scan.created_at).toLocaleString()}</td>
                  <td className="p-4 font-mono">{scan.risk_score}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      scan.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-400' :
                      scan.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {scan.risk_level}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <Link href={`/results/${scan.id}`} className="text-blue-400 hover:text-blue-300 font-medium text-sm">
                      View Report
                    </Link>
                  </td>
                </tr>
              ))}
              {stats.recent_activity.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-gray-500">No recent activity found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
