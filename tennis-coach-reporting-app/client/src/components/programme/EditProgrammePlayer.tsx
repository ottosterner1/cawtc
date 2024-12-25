import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';

interface Coach {
  id: number;
  name: string;
  email: string;
}

interface Group {
  id: number;
  name: string;
}

interface PlayerData {
  student: {
    name: string;
    date_of_birth: string | null;
    contact_email: string;
  };
  coach_id: number;
  group_id: number;
}

interface FormData {
  student_name: string;
  date_of_birth: string;
  contact_email: string;
  coach_id: string;
  group_id: string;
}

const EditProgrammePlayer: React.FC = () => {
  // Parse URL to get club ID and player ID
  const urlParts = window.location.pathname.split('/');
  const clubId = urlParts[3]; // /clubs/manage/:clubId/players/:playerId/edit
  const playerId = urlParts[urlParts.length - 2];

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData>({
    student_name: '',
    date_of_birth: '',
    contact_email: '',
    coach_id: '',
    group_id: ''
  });
  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);

  useEffect(() => {
    const fetchData = async (): Promise<void> => {
      try {
        // Extract player ID correctly from URL
        const urlParts = window.location.pathname.split('/');
        const playerId = urlParts[urlParts.length - 2]; // Gets the ID from the URL
        console.log('Fetching data for playerId:', playerId);

        const [playerRes, coachesRes, groupsRes] = await Promise.all([
          fetch(`/clubs/api/players/${playerId}`),
          fetch('/clubs/api/coaches'),
          fetch('/clubs/api/groups')
        ]);

        if (!playerRes.ok || !coachesRes.ok || !groupsRes.ok) {
          throw new Error('Failed to fetch data');
        }

        const [playerData, coachesData, groupsData] = await Promise.all([
          playerRes.json() as Promise<PlayerData>,
          coachesRes.json() as Promise<Coach[]>,
          groupsRes.json() as Promise<Group[]>
        ]);

        console.log('Fetched player data:', playerData);
        console.log('Fetched coaches:', coachesData);
        
        setFormData({
          student_name: playerData.student.name,
          date_of_birth: playerData.student.date_of_birth || '',
          contact_email: playerData.student.contact_email,
          coach_id: playerData.coach_id.toString(), // Ensure this is a string
          group_id: playerData.group_id.toString()
        });
        
        console.log('Setting coaches:', coachesData);
        setCoaches(coachesData);
        setGroups(groupsData);

        // After setting data, log the current form data
        console.log('Form data set to:', {
          student_name: playerData.student.name,
          date_of_birth: playerData.student.date_of_birth || '',
          contact_email: playerData.student.contact_email,
          coach_id: playerData.coach_id.toString(),
          group_id: playerData.group_id.toString()
        });
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load player data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch(`/clubs/api/players/${playerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          coach_id: parseInt(formData.coach_id),
          group_id: parseInt(formData.group_id)
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update player');
      }

      window.location.href = `/clubs/manage/${clubId}/players`;
    } catch (err) {
      console.error('Error updating player:', err);
      setError('Failed to update player');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (): Promise<void> => {
    if (window.confirm('Are you sure you want to remove this player from the programme?')) {
      try {
        const response = await fetch(`/clubs/api/players/${playerId}`, { method: 'DELETE' });
        if (!response.ok) {
          throw new Error('Failed to delete player');
        }
        window.location.href = `/clubs/manage/${clubId}/players`;
      } catch (err) {
        console.error('Error deleting player:', err);
        setError('Failed to delete player');
      }
    }
  };

  const handleCancel = (): void => {
    window.location.href = `/clubs/manage/${clubId}/players`;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>): void => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        <h1 className="text-2xl font-bold mb-6">Edit Programme Player</h1>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="student_name" className="block text-sm font-medium text-gray-700">
                Student Name
              </label>
              <input
                id="student_name"
                name="student_name"
                type="text"
                value={formData.student_name}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700">
                Date of Birth
              </label>
              <input
                id="date_of_birth"
                name="date_of_birth"
                type="date"
                value={formData.date_of_birth}
                onChange={handleInputChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="contact_email" className="block text-sm font-medium text-gray-700">
                Contact Email
              </label>
              <input
                id="contact_email"
                name="contact_email"
                type="email"
                value={formData.contact_email}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="coach_id" className="block text-sm font-medium text-gray-700">
                Coach
              </label>
              <select
                id="coach_id"
                name="coach_id"
                value={formData.coach_id}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                {coaches.map(coach => (
                  <option key={coach.id} value={coach.id}>{coach.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label htmlFor="group_id" className="block text-sm font-medium text-gray-700">
                Group
              </label>
              <select
                id="group_id"
                name="group_id"
                value={formData.group_id}
                onChange={handleInputChange}
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                {groups.map(group => (
                  <option key={group.id} value={group.id}>{group.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-between items-center">
            <button
              type="button"
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
            >
              Remove from Programme
            </button>

            <div className="flex space-x-3">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default EditProgrammePlayer;