import { useEffect, useState } from 'react';
import Dashboard from './components/dashboard/Dashboard';
import NavigationBar from './components/layout/NavigationBar';
import { User } from './types/user';

const App = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch('/api/current-user');
        if (response.ok) {
          const userData = await response.json();
          setCurrentUser(userData);
        }
      } catch (error) {
        console.error('Error fetching user data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCurrentUser();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!currentUser) {
    return null;
  }

  // Check if we're in the dashboard page by looking for the react-root element
  const isDashboardPage = document.getElementById('react-root')?.closest('.w-full');

  // If we're not in the dashboard page, only render the NavigationBar
  if (!isDashboardPage) {
    return <NavigationBar currentUser={currentUser} />;
  }

  // Otherwise render the full dashboard view
  return (
    <div className="w-full flex flex-col">
      <NavigationBar currentUser={currentUser} />
      <Dashboard />
    </div>
  );
};

export default App;