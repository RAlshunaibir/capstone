import React, { useState } from 'react';
import { API_ENDPOINTS } from '../config';

export default function AuthForm({ onAuthSuccess }) {
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setError('');
    const endpoint = mode === 'login' ? '/login' : '/signup';
    const payload = mode === 'login'
      ? { username: form.username, password: form.password }
      : { username: form.username, email: form.email, password: form.password };

    try {
      const res = await fetch(endpoint === '/login' ? API_ENDPOINTS.LOGIN : API_ENDPOINTS.SIGNUP, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Authentication failed');
        return;
      }
      if (mode === 'login') {
        localStorage.setItem('token', data.access_token);
        onAuthSuccess({
          username: data.username,
          access_token: data.access_token
        });
      } else {
        // On signup, switch to login mode
        setMode('login');
        setError('Signup successful! Please log in.');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-logo-title">
        <span className="auth-logo">🤖</span>
        <h1 className="auth-title">Qwen Chatbot</h1>
        <p className="auth-welcome">Welcome! Please log in or sign up to start chatting.</p>
      </div>
      <form className="auth-form" onSubmit={handleSubmit}>
        <h2>{mode === 'login' ? 'Login' : 'Sign Up'}</h2>
        <input
          name="username"
          placeholder="Username"
          value={form.username}
          onChange={handleChange}
          required
        />
        {mode === 'signup' && (
          <input
            name="email"
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={handleChange}
            required
          />
        )}
        <input
          name="password"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
          required
        />
        <button type="submit">{mode === 'login' ? 'Login' : 'Sign Up'}</button>
        {error && <div className="auth-error">{error}</div>}
        <div className="auth-toggle">
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <span onClick={() => setMode('signup')}>Sign up</span>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <span onClick={() => setMode('login')}>Login</span>
            </>
          )}
        </div>
      </form>
    </div>
  );
} 