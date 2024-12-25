// src/components/programme/ProgrammeManagement.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Download, PlusCircle, Pencil } from 'lucide-react';

interface TeachingPeriod {
  id: number;
  name: string;
}

interface Player {
  id: number;
  student_name: string;
  group_name: string;
  report_submitted: boolean;
  report_id: number | null;
  can_edit: boolean;
}

// PeriodFilter Component
const PeriodFilter: React.FC<{
  periods: TeachingPeriod[];
  selectedPeriod: number | null;
  onPeriodChange: (periodId: number) => void;
}> = ({ periods, selectedPeriod, onPeriodChange }) => (
  <div className="mb-6">
    <div className="flex items-center space-x-2">
      <label htmlFor="period" className="block text-sm font-medium text-gray-700">
        Teaching Period:
      </label>
      <select
        id="period"
        value={selectedPeriod || ''}
        onChange={(e) => onPeriodChange(Number(e.target.value))}
        className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
      >
        {periods.map((period) => (
          <option key={period.id} value={period.id}>
            {period.name}
          </option>
        ))}
      </select>
    </div>
  </div>
);

// PlayersList Component
const PlayersList: React.FC<{
  players: Player[];
  loading: boolean;
  clubId: number;
}> = ({ players, loading, clubId }) => {
  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
        <p className="mt-2 text-gray-600">Loading players...</p>
      </div>
    );
  }

  if (!players.length) {
    return (
      <div className="text-center py-8 bg-gray-50 rounded-lg">
        No players found for this teaching period.
      </div>
    );
  }

  return (
    <div className="mt-8">
      <h2 className="text-lg font-semibold mb-4">Current Players</h2>
      <div className="overflow-x-auto shadow ring-1 ring-black ring-opacity-5 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Student
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Group
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {players.map((player) => (
              <tr key={player.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium text-gray-900">{player.student_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {player.group_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {player.report_submitted ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Completed
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Pending
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  {player.can_edit && (
                    <button
                      onClick={() => window.location.href = `/clubs/manage/${clubId}/players/${player.id}/edit`}
                      className="inline-flex items-center px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-md hover:bg-indigo-100 transition-colors"
                    >
                      <Pencil className="h-4 w-4 mr-1" />
                      Edit
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// BulkUploadSection Component (imported from your existing file)
import BulkUploadSection from './BulkUploadSection';

// Main ProgrammeManagement Component
const ProgrammeManagement = () => {
  const [clubId, setClubId] = useState<number | null>(null);
  const [periods, setPeriods] = useState<TeachingPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBulkUpload, setShowBulkUpload] = useState(false);

  // Fetch club ID and user data
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await fetch('/api/current-user');
        if (!response.ok) throw new Error('Failed to fetch user data');
        const userData = await response.json();
        setClubId(userData.tennis_club.id);
      } catch (err) {
        setError('Failed to load user data');
        console.error('Error:', err);
      }
    };

    fetchUserData();
  }, []);

  // Fetch players based on selected period
  const fetchPlayers = useCallback(async () => {
    if (!selectedPeriod) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/programme-players?period=${selectedPeriod}`);
      if (!response.ok) throw new Error('Failed to fetch players');
      const data = await response.json();
      setPlayers(data);
    } catch (err) {
      setError('Failed to load players');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedPeriod]);

  // Fetch periods on component mount
  useEffect(() => {
    const fetchPeriods = async () => {
      try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) throw new Error('Failed to fetch periods');
        const data = await response.json();
        setPeriods(data.periods);
        if (data.periods.length > 0) {
          setSelectedPeriod(data.periods[0].id);
        }
      } catch (err) {
        setError('Failed to load teaching periods');
        console.error('Error:', err);
      }
    };

    fetchPeriods();
  }, []);

  // Fetch players when selected period changes
  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

  const handleBulkUploadSuccess = () => {
    fetchPlayers();
    setShowBulkUpload(false);
  };

  const handleDownloadTemplate = () => {
    window.location.href = `/clubs/api/template/download`;
  };

  const handleAddPlayer = () => {
    window.location.href = `/clubs/manage/${clubId}/players/add`;
  };

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!clubId) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <Card>
        <CardContent>
          {/* Period Filter */}
          <PeriodFilter
            periods={periods}
            selectedPeriod={selectedPeriod}
            onPeriodChange={setSelectedPeriod}
          />

          {/* Header with Actions */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 space-y-4 md:space-y-0">
            <h1 className="text-2xl font-bold text-gray-900">
              Manage Programme Players
            </h1>

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              <button
                onClick={handleAddPlayer}
                className="inline-flex items-center justify-center px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                <PlusCircle className="h-5 w-5 mr-2" />
                Add New Player
              </button>
              <button
                onClick={() => setShowBulkUpload(!showBulkUpload)}
                className="inline-flex items-center justify-center px-4 py-2 bg-indigo-500 text-white rounded-md hover:bg-indigo-600 transition-colors"
              >
                Bulk Upload
              </button>
              <button
                onClick={handleDownloadTemplate}
                className="inline-flex items-center justify-center px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
              >
                <Download className="h-5 w-5 mr-2" />
                Download Template
              </button>
            </div>
          </div>

          {/* Bulk Upload Section */}
          {showBulkUpload && (
            <BulkUploadSection
              periodId={selectedPeriod}
              onSuccess={handleBulkUploadSuccess}
              onCancel={() => setShowBulkUpload(false)}
            />
          )}

          {/* Players List */}
          <PlayersList
            players={players}
            loading={loading}
            clubId={clubId}
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default ProgrammeManagement;