import React from 'react';

const Login = () => {
  return (
    <div className="login-container">
      <h2>Login to HRMS</h2>
      <input type="email" placeholder="Email" />
      <input type="password" placeholder="Password" />
      <button>Login</button>
    </div>
  );
};

export default Login;