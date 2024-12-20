import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertTitle } from '../../components/ui/alert';

interface BulkEmailSenderProps {
  periodId: number;
  onClose: () => void;
}

export const BulkEmailSender: React.FC<BulkEmailSenderProps> = ({ periodId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [emailSubject, setEmailSubject] = useState('');
  const [emailMessage, setEmailMessage] = useState('');
  const [successCount, setSuccessCount] = useState(0);
  const [errorCount, setErrorCount] = useState(0);

  // Prevent showing the modal if no period is selected
  if (!periodId) {
    return null;
  }

  const sendEmails = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Starting email send process');
    console.log('Period ID:', periodId);
    setLoading(true);
    setError(null);
    
    try {
      // Add protocol and host if not using a proxy
      const baseUrl = import.meta.env.VITE_API_URL || '';
      const url = `${baseUrl}/api/reports/send/${periodId}`;
      console.log('Sending request to:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          email_subject: emailSubject,
          email_message: emailMessage
        })
      });
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const text = await response.text();
        console.error('Error response:', text);
        throw new Error(text);
      }
      
      const data = await response.json();
      console.log('Response data:', data);
      
      setSuccess(true);
      setSuccessCount(data.success_count || 0);
      setErrorCount(data.error_count || 0);
      
    } catch (err) {
      console.error('Error sending emails:', err);
      setError(err instanceof Error ? err.message : 'Error sending emails');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl">
        <CardHeader className="flex justify-between items-center">
          <CardTitle>Send Reports</CardTitle>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            Close
          </button>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert className="mb-4 bg-red-50">
              <AlertTitle>{error}</AlertTitle>
            </Alert>
          )}
          
          {success ? (
            <div className="text-center py-4">
              <p className="text-lg font-medium text-green-600 mb-2">
                Reports sent successfully!
              </p>
              <p>
                Successfully sent: {successCount} <br />
                Failed: {errorCount}
              </p>
              <button
                onClick={onClose}
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          ) : (
            <form onSubmit={sendEmails} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email Subject
                </label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  value={emailSubject}
                  onChange={(e) => setEmailSubject(e.target.value)}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Email Message
                </label>
                <textarea
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  rows={10}
                  value={emailMessage}
                  onChange={(e) => setEmailMessage(e.target.value)}
                  required
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Sending...' : 'Send Reports'}
                </button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};