import React from 'react';
import Login from './components/login/Login';
import Dashboard from './components/dashboard/Dashboard';
import ATSScorer from './components/ats-scorer/ATSScorer';

const App = () => {
  return (
    <div>
      <Login />
      <Dashboard />
      <ATSScorer />
    </div>
  );
};

export default App;