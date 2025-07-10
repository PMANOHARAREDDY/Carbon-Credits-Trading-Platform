import React from 'react';

function GoogleLoginButton() {
  const handleLogin = () => {
    fetch('http://localhost:5000/login')
      .then(res => res.json())
      .then(data => {
        window.location.href = data.auth_url;
      });
  };

  return (
    <button onClick={handleLogin}>
      Sign in with Google
    </button>
  );
}

export default GoogleLoginButton;
