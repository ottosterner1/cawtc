// src/entry/create_report.tsx
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import DynamicReportForm from '../components/reports/DynamicReportForm';
import '../index.css';

const CreateReportApp = () => {
  const [template, setTemplate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get data from the DOM
  const rootElement = document.getElementById('create-report-root');
  const playerId = rootElement?.dataset.playerId;
  const studentName = rootElement?.dataset.studentName ?? '';
  const groupName = rootElement?.dataset.groupName ?? '';

  useEffect(() => {
    const fetchTemplate = async () => {
      try {
        const response = await fetch(`/api/reports/template/${playerId}`);
        if (!response.ok) throw new Error('Failed to fetch template');
        const data = await response.json();
        // Store the entire template object
        setTemplate(data.template);
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

  const handleSubmit = async (formData: Record<string, any>) => {
    try {
      const response = await fetch(`/api/reports/create/${playerId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: formData,
          template_id: template?.id
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to submit report');
      }
      
      // Redirect to dashboard on success
      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Error submitting report:', err);
      throw err;
    }
  };

  if (loading) return <div className="flex justify-center items-center p-8">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">Error: {error}</div>;
  if (!template) return <div className="p-4">No template available</div>;

  // Pass the complete template data to DynamicReportForm
  return (
    <DynamicReportForm
      template={template}
      studentName={studentName}
      groupName={groupName}
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