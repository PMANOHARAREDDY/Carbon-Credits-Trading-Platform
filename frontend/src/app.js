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
      <div className="signin-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Carbon_Dioxide_Icon.svg/120px-Carbon_Dioxide_Icon.svg.png" alt="Carbon Trading Logo" className="signin-logo" />
        <h1>Welcome</h1>
        <div className="signin-tagline">Empowering Carbon Trading for a Sustainable Future</div>
        <h2>Carbon Trading Platform</h2>
        <GoogleLoginButton />
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
        <div className="bubble"></div>
      </div>
    );
  }

  if (user === BOARD_EMAIL) {
    return (
      <div className="app-container">
        <h1>Welcome Board, </h1>
        <h2>{user}</h2>
        <BoardVerify userEmail={user} setRefresh={setRefresh} refresh={refresh} />
        <a href="http://localhost:5000/logout" className="logout-link">Logout</a>
      </div>
    );
  }

  return (
    <div className="app-container">
      <h1>User : {user}</h1>
      <Onboarding userEmail={user} setRefresh={setRefresh} refresh={refresh} />
      <Dashboard userEmail={user} refresh={refresh} />
      <Marketplace userEmail={user} refresh={refresh} />
      <a href="http://localhost:5000/logout" className="logout-link">Logout</a>
    </div>
  );
}

export default App;
