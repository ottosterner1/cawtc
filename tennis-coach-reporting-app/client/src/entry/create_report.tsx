import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import DynamicReportForm from '../components/reports/DynamicReportForm';
import '../index.css';

interface FormData {
  content: Record<string, Record<string, any>>;
  recommendedGroupId: number;
  template_id: number;
}

interface PlayerData {
  studentName: string;
  dateOfBirth: string | null;
  age: number | null;
  groupName: string;
}

const CreateReportApp = () => {
  const [template, setTemplate] = useState<any>(null);
  const [playerData, setPlayerData] = useState<PlayerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get data from the DOM
  const rootElement = document.getElementById('create-report-root');
  const playerId = rootElement?.dataset.playerId;

  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const response = await fetch(`/api/reports/template/${playerId}`);
        if (!response.ok) throw new Error('Failed to fetch template');
        const data = await response.json();
        // Store the template and player data separately
        setTemplate(data.template);
        setPlayerData({
          studentName: data.player.studentName,
          dateOfBirth: data.player.dateOfBirth,
          age: data.player.age,
          groupName: data.player.groupName
        });
      } catch (err) {
        setError((err as Error).message);
        console.error('Error fetching template:', err);
      } finally {
        setLoading(false);
      }
    };

    if (playerId) {
      fetchTemplate();
    }
  }, [playerId]);

  const handleSubmit = async (data: Record<string, any>) => {
    try {
      const formData: FormData = {
        content: data.content,
        recommendedGroupId: Number(data.recommendedGroupId),
        template_id: data.template_id,
      };

      const response = await fetch(`/api/reports/create/${playerId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to submit report');
      }

      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Error submitting report:', err);
      throw err;
    }
  };

  if (loading) return <div className="flex justify-center items-center p-8">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">Error: {error}</div>;
  if (!template || !playerData) return <div className="p-4">No data available</div>;

  return (
    <DynamicReportForm
      template={template}
      studentName={playerData.studentName}
      dateOfBirth={playerData.dateOfBirth || undefined}
      age={playerData.age || undefined}
      groupName={playerData.groupName}
      onSubmit={handleSubmit}
      onCancel={() => window.location.href = '/dashboard'}
    />
  );
};

const container = document.getElementById('create-report-root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <CreateReportApp />
    </React.StrictMode>
  );
}