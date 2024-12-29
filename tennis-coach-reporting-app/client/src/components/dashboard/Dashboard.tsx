import { useState, useEffect } from 'react';
import { Download, Send } from 'lucide-react';
import { DashboardStats } from './DashboardStats';
import { BulkEmailSender } from '../email/BulkEmailSender';
import { 
  TeachingPeriod, 
  DashboardMetrics, 
  ProgrammePlayer,
  User 
} from '../../types/dashboard';

interface GroupedPlayers {
  [groupName: string]: {
    timeSlots: {
      [timeSlot: string]: ProgrammePlayer[];
    };
  };
}

interface DashboardProps {
  onCreateReport?: (playerId: number) => void;
  onEditReport?: (reportId: number) => void;
  onViewReport?: (reportId: number) => void;
}

const Dashboard: React.FC<DashboardProps> = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [periods, setPeriods] = useState<TeachingPeriod[]>([]);
  const [stats, setStats] = useState<DashboardMetrics | null>(null);
  const [players, setPlayers] = useState<ProgrammePlayer[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBulkEmail, setShowBulkEmail] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [printing, setPrinting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
  
        const userResponse = await fetch('/api/current-user');
        if (!userResponse.ok) throw new Error('Failed to fetch user data');
        const userData = await userResponse.json();
        setCurrentUser(userData);
  
        const statsResponse = await fetch(`/api/dashboard/stats${selectedPeriod ? `?period=${selectedPeriod}` : ''}`);
        if (!statsResponse.ok) throw new Error('Failed to fetch dashboard stats');
        const statsData = await statsResponse.json();
        setPeriods(statsData.periods);
        
        if (!selectedPeriod && statsData.periods.length > 0) {
          const latestPeriod = statsData.periods[statsData.periods.length - 1];
          setSelectedPeriod(latestPeriod.id);
          setStats(statsData.stats);
          return;
        }
        
        setStats(statsData.stats);
  
        const playersResponse = await fetch(`/api/programme-players${selectedPeriod ? `?period=${selectedPeriod}` : ''}`);
        if (!playersResponse.ok) throw new Error('Failed to fetch programme players');
        const playersData = await playersResponse.json();
        setPlayers(playersData);
  
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setError(error instanceof Error ? error.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };
  
    fetchData();
  }, [selectedPeriod]);

  const handleSendReportsClick = () => {
    if (!selectedPeriod) {
      alert('Please select a teaching period before sending reports');
      return;
    }
    if (!stats?.totalReports) {
      alert('There are no reports available to send');
      return;
    }
    setShowBulkEmail(true);
  };

  const handleDownloadAllReports = async () => {
    if (!selectedPeriod) {
      alert('Please select a teaching period');
      return;
    }
  
    try {
      setDownloading(true);
      const response = await fetch(`/api/reports/download-all/${selectedPeriod}`, {
        method: 'GET',
        credentials: 'include'
      });
  
      if (!response.ok) {
        if (response.headers.get('content-type')?.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate reports');
        }
        throw new Error('Failed to download reports');
      }
  
      const blob = await response.blob();
      
      // Get filename from Content-Disposition header or use a default
      let filename = 'reports.zip';
      const contentDisposition = response.headers.get('Content-Disposition');
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }
  
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
  
    } catch (error) {
      console.error('Error downloading reports:', error);
      alert('Error downloading reports: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setDownloading(false);
    }
  };

  const handlePrintAllReports = async () => {
    if (!selectedPeriod) {
      alert('Please select a teaching period');
      return;
    }
  
    try {
      setPrinting(true);
      const response = await fetch(`/api/reports/print-all/${selectedPeriod}`, {
        method: 'GET',
        credentials: 'include'
      });
  
      if (!response.ok) {
        if (response.headers.get('content-type')?.includes('application/json')) {
          const errorData = await response.json();
          throw new Error(errorData.error || 'Failed to generate combined report');
        }
        throw new Error('Failed to print reports');
      }
  
      // Get the PDF blob
      const blob = await response.blob();
      
      // Create URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Open in a new window
      window.open(url, '_blank');
      
      // Clean up
      window.URL.revokeObjectURL(url);
  
    } catch (error) {
      console.error('Error printing reports:', error);
      alert('Error printing reports: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setPrinting(false);
    }
  };

  const groupPlayersByGroupAndTime = (players: ProgrammePlayer[]): GroupedPlayers => {
    return players.reduce((acc: GroupedPlayers, player) => {
      const groupName = player.group_name;
      const timeSlot = player.time_slot ? 
        `${player.time_slot.day_of_week} ${player.time_slot.start_time}-${player.time_slot.end_time}` : 
        'Unscheduled';

      if (!acc[groupName]) {
        acc[groupName] = { timeSlots: {} };
      }
      if (!acc[groupName].timeSlots[timeSlot]) {
        acc[groupName].timeSlots[timeSlot] = [];
      }
      acc[groupName].timeSlots[timeSlot].push(player);
      return acc;
    }, {});
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (!stats || !currentUser) return <div>No data available</div>;

  const groupedPlayers = groupPlayersByGroupAndTime(players);

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Tennis Reports Dashboard</h1>
        <div className="flex items-center gap-4">
          <select
            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            value={selectedPeriod || ''}
            onChange={(e) => setSelectedPeriod(e.target.value ? Number(e.target.value) : null)}
          >
            {periods.map((period) => (
              <option key={period.id} value={period.id}>{period.name}</option>
            ))}
          </select>

          {(currentUser?.is_admin || currentUser?.is_super_admin) && (
            <div className="flex gap-2">
              <button
                onClick={handleDownloadAllReports}
                disabled={!selectedPeriod || !stats?.totalReports || downloading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Download className="w-4 h-4" />
                {downloading ? 'Downloading...' : 'Download All Reports'}
                {stats?.totalReports > 0 && !downloading && (
                  <span className="bg-blue-500 px-2 py-0.5 rounded-full text-sm">
                    {stats.totalReports}
                  </span>
                )}
              </button>

              <button
                onClick={handlePrintAllReports}
                disabled={!selectedPeriod || !stats?.totalReports || printing}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {printing ? 'Preparing...' : 'Print All Reports'}
                {stats?.totalReports > 0 && !printing && (
                  <span className="bg-purple-500 px-2 py-0.5 rounded-full text-sm">
                    {stats.totalReports}
                  </span>
                )}
              </button>

              <button
                onClick={handleSendReportsClick}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!selectedPeriod || !stats?.totalReports}
              >
                <Send className="w-4 h-4" />
                Send Reports
                {stats?.totalReports > 0 && (
                  <span className="bg-green-500 px-2 py-0.5 rounded-full text-sm">
                    {stats.totalReports}
                  </span>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      <DashboardStats stats={stats} />

      {/* Modal for Bulk Email */}
      {showBulkEmail && selectedPeriod && (
        <BulkEmailSender
          periodId={selectedPeriod}
          onClose={() => setShowBulkEmail(false)}
        />
      )}

      {/* Admin Analytics Section */}
      {(currentUser.is_admin || currentUser.is_super_admin) && stats.coachSummaries && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Group Progress Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Group Progress</h3>
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
              {stats.currentGroups.map((group) => (
                <div 
                  key={group.name} 
                  className="p-3 bg-gray-50 rounded-lg flex flex-col"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{group.name}</span>
                    <span className="text-sm text-gray-500">{group.count} players</span>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${((group.reports_completed / group.count) * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 mt-1 self-end">
                    {((group.reports_completed / group.count) * 100).toFixed(1)}% complete
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Coach Reports Progress Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Coach Progress</h3>
            <div className="space-y-3 max-h-[300px] overflow-y-auto">
              {stats.coachSummaries.map((coach) => (
                <div 
                  key={coach.id} 
                  className="p-3 bg-gray-50 rounded-lg flex flex-col"
                >
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-900">{coach.name}</span>
                    <span className="text-sm text-gray-500">
                      {coach.reports_completed}/{coach.total_assigned}
                    </span>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${((coach.reports_completed / coach.total_assigned) * 100)}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 mt-1 self-end">
                    {((coach.reports_completed / coach.total_assigned) * 100).toFixed(1)}% complete
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Group Recommendations Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Group Recommendations</h3>
            {stats.groupRecommendations && stats.groupRecommendations.length > 0 ? (
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {Object.entries(
                  stats.groupRecommendations.reduce((acc, rec) => {
                    acc[rec.to_group] = (acc[rec.to_group] || 0) + rec.count;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([group, count]) => (
                  <div 
                    key={group} 
                    className="p-3 bg-gray-50 rounded-lg flex justify-between items-center"
                  >
                    <span className="font-medium text-gray-900">{group}</span>
                    <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                      {count} {count === 1 ? 'player' : 'players'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                No recommendations for this period
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reports Management Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-6">
          {currentUser.is_admin || currentUser.is_super_admin ? 'All Reports' : 'Reports'}
        </h2>
        
        {Object.keys(groupedPlayers).length === 0 ? (
          <p className="text-gray-500">No reports available for this period.</p>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedPlayers).map(([groupName, group]) => (
              <div key={groupName} className="space-y-4">
                <div className="border-b pb-2">
                  <h3 className="text-xl font-medium text-gray-900">{groupName}</h3>
                </div>
                
                <div className="space-y-6">
                  {Object.entries(group.timeSlots).map(([timeSlot, players]) => (
                    <div key={timeSlot} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-4">
                        <h4 className="font-medium text-gray-900">{timeSlot}</h4>
                        <span className="text-sm text-gray-500">
                          {players.filter(p => p.report_submitted).length}/{players.length} reports completed
                        </span>
                      </div>
                      
                      <div className="bg-white rounded-lg divide-y">
                        {players.map((player) => (
                          <div key={player.id} className="p-4 flex justify-between items-center">
                            <div>
                              <h3 className="font-medium">{player.student_name}</h3>
                              {player.report_submitted ? (
                                <span className="text-sm text-green-600">Report submitted</span>
                              ) : (
                                <span className="text-sm text-amber-600">Report pending</span>
                              )}
                            </div>
                            {/* Modify the actions section in your player mapping */}
                            <div className="space-x-2">
                              {player.report_submitted ? (
                                <>
                                  <a 
                                    href={`/reports/${player.report_id}`}
                                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                                  >
                                    View
                                  </a>
                                  {player.can_edit && (
                                    <a
                                      href={`/reports/${player.report_id}/edit`}
                                      className="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50"
                                    >
                                      Edit
                                    </a>
                                  )}
                                </>
                              ) : (
                                player.can_edit && player.has_template ? (
                                  <a 
                                    href={`/report/new/${player.id}`}
                                    className="inline-flex items-center px-3 py-2 border border-green-300 shadow-sm text-sm font-medium rounded-md text-green-700 bg-white hover:bg-green-50"
                                  >
                                    Create Report
                                  </a>
                                ) : (
                                  <span className="text-sm text-gray-500 italic">
                                    No Report Available
                                  </span>
                                )
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;