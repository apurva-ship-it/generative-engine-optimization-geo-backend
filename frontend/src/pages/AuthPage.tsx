import React, { useState } from 'react';
import * as yup from 'yup';

const schema = yup.object().shape({
  email: yup.string().email('Invalid email').required('Email required'),
  password: yup.string().min(6, 'Password too short').required('Password required'),
  name: yup.string().when('$isLogin', {
    is: false,
    then: yup.string().required('Name required'),
  }),
});

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({ email: '', password: '', name: '' });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await schema.validate(form, { abortEarly: false, context: { isLogin } });
      setErrors({});
      const endpoint = isLogin ? '/api/v1/auth/login' : '/api/v1/users';
      const body: Record<string, any> = { email: form.email, password: form.password };
      if (!isLogin) body.name = form.name;
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Request failed');
      }
      window.location.href = '/';
    } catch (err: any) {
      if (err.name === 'ValidationError') {
        const fieldErrors: { [key: string]: string } = {};
        err.inner.forEach((e: any) => {
          fieldErrors[e.path] = e.message;
        });
        setErrors(fieldErrors);
      } else {
        setErrors({ form: err.message });
      }
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: 'auto', padding: '1rem' }}>
      <h2>{isLogin ? 'Login' : 'Register'}</h2>
      <form onSubmit={handleSubmit} noValidate>
        {!isLogin && (
          <div style={{ marginBottom: 8 }}>
            <label>Name:</label>
            <input
              type="text"
              name="name"
              value={form.name}
              onChange={handleChange}
            />
            {errors.name && <div style={{ color: 'red' }}>{errors.name}</div>}
          </div>
        )}
        <div style={{ marginBottom: 8 }}>
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={form.email}
            onChange={handleChange}
          />
          {errors.email && <div style={{ color: 'red' }}>{errors.email}</div>}
        </div>
        <div style={{ marginBottom: 8 }}>
          <label>Password:</label>
          <input
            type="password"
            name="password"
            value={form.password}
            onChange={handleChange}
          />
          {errors.password && <div style={{ color: 'red' }}>{errors.password}</div>}
        </div>
        {errors.form && <div style={{ color: 'red' }}>{errors.form}</div>}
        <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
      </form>
      <p style={{ marginTop: 12 }}>
        {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
        <button
          onClick={() => setIsLogin(!isLogin)}
          style={{ background: 'none', border: 'none', color: 'blue', textDecoration: 'underline', cursor: 'pointer' }}
        >
          {isLogin ? 'Register' : 'Login'}
        </button>
      </p>
    </div>
  );
};

export default AuthPage;
