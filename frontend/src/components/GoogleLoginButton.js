import React from 'react';


import './GoogleLoginButton.css';

function GoogleLoginButton() {
  const handleLogin = () => {
    fetch('http://localhost:5000/login')
      .then(res => res.json())
      .then(data => {
        window.location.href = data.auth_url;
      });
  };

  return (
    <button className="google-login-button" onClick={handleLogin} aria-label="Sign in with Google">
      <svg className="google-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 533.5 544.3" aria-hidden="true">
        <path fill="#4285f4" d="M533.5 278.4c0-18.5-1.5-36.3-4.3-53.6H272v101.4h146.9c-6.3 34-25.4 62.8-54.3 82v68h87.7c51.3-47.3 81.2-116.8 81.2-197.8z"/>
        <path fill="#34a853" d="M272 544.3c73.7 0 135.6-24.4 180.8-66.1l-87.7-68c-24.4 16.3-55.7 25.9-93.1 25.9-71.5 0-132-48.3-153.5-113.1H29.6v70.9c45.1 89.1 137.7 150.4 242.4 150.4z"/>
        <path fill="#fbbc04" d="M118.5 321.1c-10.7-31.8-10.7-66.3 0-98.1v-70.9H29.6c-38.6 75.3-38.6 164.7 0 240l88.9-70.9z"/>
        <path fill="#ea4335" d="M272 107.7c39.9 0 75.7 13.7 104 40.7l78-78C405.7 24.4 343.8 0 272 0 167.3 0 74.7 61.3 29.6 150.4l88.9 70.9c21.5-64.8 82-113.6 153.5-113.6z"/>
      </svg>
      Sign in with Google
    </button>
  );
}

export default GoogleLoginButton;
