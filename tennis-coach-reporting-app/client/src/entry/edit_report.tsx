// src/entry/edit_report.tsx
import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import DynamicReportForm from '../components/reports/DynamicReportForm';
import '../index.css';

const EditReportApp = () => {
  const [report, setReport] = useState<any>(null);
  const [template, setTemplate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get report ID from the DOM
  const rootElement = document.getElementById('edit-report-root');
  const reportId = rootElement?.dataset.reportId;

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const response = await fetch(`/api/reports/${reportId}`);
        if (!response.ok) throw new Error('Failed to fetch report');
        const data = await response.json();
        setReport(data.report);
        setTemplate(data.template);
      } catch (err) {
        setError((err as Error).message);
        console.error('Error fetching report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (reportId) {
      fetchReport();
    }
  }, [reportId]);

  const handleSubmit = async (formData: Record<string, any>) => {
    try {
      const response = await fetch(`/api/reports/${reportId}`, {
        method: 'PUT',
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
        throw new Error(errorData.error || 'Failed to update report');
      }
      
      // Redirect to view report page on success
      window.location.href = `/report/${reportId}`;
    } catch (err) {
      console.error('Error updating report:', err);
      throw err;
    }
  };

  if (loading) return <div className="flex justify-center items-center p-8">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">Error: {error}</div>;
  if (!report || !template) return <div className="p-4">No report available</div>;

  return (
    <div className="p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">Edit Report</h1>
      </div>
      <DynamicReportForm
        template={template}
        studentName={report.studentName}
        groupName={report.groupName}
        initialData={report.content}
        onSubmit={handleSubmit}
        onCancel={() => window.location.href = `/report/${reportId}`}
      />
    </div>
  );
};

const container = document.getElementById('edit-report-root');
if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <EditReportApp />
    </React.StrictMode>
  );
}