import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import DynamicReportForm from '../components/reports/DynamicReportForm';
import '../index.css';

const EditReportApp = () => {
  const [report, setReport] = useState<any>(null);
  const [template, setTemplate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

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
      
      window.location.href = `/reports/${reportId}`;
    } catch (err) {
      console.error('Error updating report:', err);
      throw err;
    }
  };

  const handleDelete = async () => {
    try {
      const response = await fetch(`/reports/delete/${reportId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to delete report');
      }

      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Error deleting report:', err);
      setError('Failed to delete report');
    }
  };

  if (loading) return <div className="flex justify-center items-center p-8">Loading...</div>;
  if (error) return <div className="text-red-500 p-4">Error: {error}</div>;
  if (!report || !template) return <div className="p-4">No report available</div>;

  return (
    <div className="p-4">
      <div className="mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Edit Report</h1>
        <button 
          onClick={() => setShowDeleteDialog(true)}
          className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
        >
          Delete Report
        </button>
      </div>

      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-lg font-semibold mb-4">Delete Report</h2>
            <p className="mb-6">Are you sure you want to delete this report? This action cannot be undone.</p>
            <div className="flex justify-end gap-4">
              <button
                onClick={() => setShowDeleteDialog(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <DynamicReportForm
        template={template}
        studentName={report.studentName}
        groupName={report.groupName}
        initialData={report.content}
        onSubmit={handleSubmit}
        onCancel={() => window.location.href = `/reports/${reportId}`}
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

export default EditReportApp;