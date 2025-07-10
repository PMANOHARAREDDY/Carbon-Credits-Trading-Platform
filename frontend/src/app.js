import React, { useState, useEffect } from 'react';
import GoogleLoginButton from './components/GoogleLoginButton';
import Onboarding from './components/Onboarding';
import Dashboard from './components/Dashboard';
import Marketplace from './components/Marketplace';
import BoardVerify from './components/BoardVerify';

const BOARD_EMAIL = "manoharareddyp97@gmail.com";

function App() {
  const [user, setUser] = useState(null);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const email = params.get('user');
    if (email) setUser(email);
  }, []);

  if (!user) {
    return (
      <div>
        <h1>Carbon Credit Platform</h1>
        <GoogleLoginButton />
      </div>
    );
  }

  if (user === BOARD_EMAIL) {
    return (
      <div>
        <h1>Welcome, Board ({user})</h1>
        <BoardVerify userEmail={user} setRefresh={setRefresh} refresh={refresh} />
        <a href="http://localhost:5000/logout">Logout</a>
      </div>
    );
  }

  return (
    <div>
      <h1>Welcome, {user}</h1>
      <Onboarding userEmail={user} setRefresh={setRefresh} refresh={refresh} />
      <Dashboard userEmail={user} refresh={refresh} />
      <Marketplace userEmail={user} refresh={refresh} />
      <a href="http://localhost:5000/logout">Logout</a>
    </div>
  );
}

export default App;
