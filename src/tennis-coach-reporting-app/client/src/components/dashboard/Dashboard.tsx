import { useState } from 'react';
import axios from 'axios';
import { useQuery } from '@tanstack/react-query';

// TypeScript interfaces
interface Period {
  id: number;
  name: string;
}

interface Player {
  id: number;
  student_name: string;
  student_age: number;
  group_name: string;
  coach_name: string;
  has_report: boolean;
  report_id: number | null;
}

interface GroupSummary {
  name: string;
  count: number;
}

interface DashboardData {
  periods: Period[];
  players: Player[];
  current_groups: GroupSummary[];
  recommended_groups: GroupSummary[];
  is_admin: boolean;
}

const fetchDashboardData = async (periodId: number | null): Promise<DashboardData> => {
  try {
    const { data } = await axios.get<DashboardData>(`/api/dashboard${periodId ? `?period=${periodId}` : ''}`);
    return data;
  } catch (error) {
    throw new Error('Failed to fetch dashboard data');
  }
};

export default function Dashboard(): JSX.Element {
  const [selectedPeriodId, setSelectedPeriodId] = useState<number | null>(null);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', selectedPeriodId],
    queryFn: () => fetchDashboardData(selectedPeriodId),
    refetchOnWindowFocus: false,
    retry: 1
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-red-600 p-4">
        {error?.message || 'Error loading dashboard data'}
      </div>
    );
  }

  const handlePeriodChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedPeriodId(value ? Number(value) : null);
  };

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Reports Dashboard</h1>

      <div className="mb-6">
        <div className="flex justify-between items-center gap-4">
          <div className="w-64">
            <label htmlFor="period" className="block text-sm font-medium text-gray-700">
              Select Teaching Period:
            </label>
            <select
              id="period"
              value={selectedPeriodId || ''}
              onChange={handlePeriodChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {data.periods.map((period) => (
                <option key={period.id} value={period.id}>
                  {period.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Group Summary Section */}
      <div className="grid gap-4 mb-6 md:grid-cols-2">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Current Groups</h3>
            <div className="space-y-2">
              {data.current_groups.map((group) => (
                <div key={group.name} className="flex justify-between items-center">
                  <span className="font-medium">{group.name}</span>
                  <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {group.count} players
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Recommended Future Groups
            </h3>
            <div className="space-y-2">
              {data.recommended_groups.map((group) => (
                <div key={group.name} className="flex justify-between items-center">
                  <span className="font-medium">{group.name}</span>
                  <span className="text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    {group.count} players
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Student
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Age
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Group
              </th>
              {data.is_admin && (
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Coach
                </th>
              )}
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Report Status
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.players.map((player) => (
              <tr key={player.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {player.student_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {player.student_age}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {player.group_name}
                </td>
                {data.is_admin && (
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {player.coach_name}
                  </td>
                )}
                <td className="px-6 py-4 whitespace-nowrap">
                  {player.has_report ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Submitted
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Pending
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {player.has_report ? (
                        <div className="flex space-x-2">
                        <a             
                            href={`/report/${player.report_id}/edit?period=${selectedPeriodId}`}
                            className="text-indigo-600 hover:text-indigo-900"
                        >
                            Edit Report
                        </a>            
                        <a              
                            href={`/report/${player.report_id}?period=${selectedPeriodId}`}
                            className="text-green-600 hover:text-green-900"
                        >
                            View Report
                        </a>            
                        </div>
                    ) : (
                        <a              
                        href={`/report/create/${player.id}?period=${selectedPeriodId}`}
                        className="text-indigo-600 hover:text-indigo-900"
                        >
                        Create Report
                        </a> 
                    )}
                    </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}