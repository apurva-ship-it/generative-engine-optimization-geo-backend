import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as yup from 'yup';
const registerSchema = yup.object({
    fullName: yup.string().required('Full name is required'),
    email: yup.string().email('Invalid email').required('Email is required'),
    mobile: yup
        .string()
        .matches(/^\d{10}$/, 'Mobile must be exactly 10 digits')
        .required('Mobile number is required'),
    age: yup
        .number()
        .typeError('Age must be a number')
        .integer('Age must be a whole number')
        .min(1, 'Age must be at least 1')
        .max(120, 'Age must be at most 120')
        .required('Age is required'),
    sex: yup.string().oneOf(['Male', 'Female', 'Other']).required('Sex is required'),
    password: yup.string().min(6, 'Password must be at least 6 characters').required('Password is required'),
});
const loginSchema = yup.object({
    email: yup.string().email('Invalid email').required('Email is required'),
    password: yup.string().min(6, 'Password must be at least 6 characters').required('Password is required'),
});
const inputStyle = {
    display: 'block', width: '100%', padding: '8px 12px',
    border: '1px solid #ccc', borderRadius: 6, fontSize: 14,
    marginTop: 4,
};
const labelStyle = {
    display: 'block', fontSize: 13, fontWeight: 600, color: '#444',
};
const fieldWrap = { marginBottom: 14 };
const errStyle = { color: '#e53935', fontSize: 12, marginTop: 3 };
const AuthPage = () => {
    const navigate = useNavigate();
    const [isLogin, setIsLogin] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [globalErr, setGlobalErr] = useState('');
    const [errors, setErrors] = useState({});
    const [form, setForm] = useState({
        fullName: '', email: '', mobile: '', age: '', sex: '', password: '',
    });
    const handleChange = (e) => {
        setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
        setErrors(prev => ({ ...prev, [e.target.name]: '' }));
        setGlobalErr('');
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        setGlobalErr('');
        setErrors({});
        try {
            if (isLogin) {
                await loginSchema.validate({ email: form.email, password: form.password }, { abortEarly: false });
            }
            else {
                await registerSchema.validate({ ...form, age: form.age === '' ? undefined : Number(form.age) }, { abortEarly: false });
            }
        }
        catch (err) {
            if (err.name === 'ValidationError') {
                const fieldErrors = {};
                err.inner.forEach((e) => { fieldErrors[e.path] = e.message; });
                setErrors(fieldErrors);
            }
            return;
        }
        setSubmitting(true);
        try {
            const endpoint = isLogin ? '/api/v1/auth/login' : '/api/v1/users';
            const payload = isLogin
                ? { email: form.email, password: form.password }
                : { fullName: form.fullName, email: form.email, mobile: form.mobile, age: Number(form.age), sex: form.sex, password: form.password };
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(payload),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                setGlobalErr(data.error || (isLogin ? 'Login failed' : 'Registration failed'));
                return;
            }
            navigate('/');
        }
        catch {
            setGlobalErr('Network error — is the backend running?');
        }
        finally {
            setSubmitting(false);
        }
    };
    const card = {
        maxWidth: 420, margin: '60px auto', background: '#fff',
        borderRadius: 10, padding: '32px 36px',
        boxShadow: '0 2px 16px rgba(0,0,0,0.1)',
    };
    return (_jsx("div", { style: { background: '#f5f5f5', minHeight: '100vh' }, children: _jsxs("div", { style: card, children: [_jsx("h2", { style: { marginBottom: 24, textAlign: 'center', color: '#222' }, children: isLogin ? 'Login' : 'Create account' }), _jsxs("form", { onSubmit: handleSubmit, noValidate: true, children: [!isLogin && (_jsx(_Fragment, { children: _jsxs("div", { style: fieldWrap, children: [_jsx("label", { style: labelStyle, children: "Full Name" }), _jsx("input", { style: inputStyle, type: "text", name: "fullName", placeholder: "Jane Doe", value: form.fullName, onChange: handleChange }), errors.fullName && _jsx("div", { style: errStyle, children: errors.fullName })] }) })), _jsxs("div", { style: fieldWrap, children: [_jsx("label", { style: labelStyle, children: "Email" }), _jsx("input", { style: inputStyle, type: "email", name: "email", placeholder: "you@example.com", value: form.email, onChange: handleChange }), errors.email && _jsx("div", { style: errStyle, children: errors.email })] }), !isLogin && (_jsxs(_Fragment, { children: [_jsxs("div", { style: fieldWrap, children: [_jsx("label", { style: labelStyle, children: "Mobile Number" }), _jsx("input", { style: inputStyle, type: "tel", name: "mobile", placeholder: "10-digit number", maxLength: 10, value: form.mobile, onChange: handleChange }), errors.mobile && _jsx("div", { style: errStyle, children: errors.mobile })] }), _jsxs("div", { style: { display: 'flex', gap: 12, marginBottom: 14 }, children: [_jsxs("div", { style: { flex: 1 }, children: [_jsx("label", { style: labelStyle, children: "Age" }), _jsx("input", { style: inputStyle, type: "number", name: "age", placeholder: "25", min: 1, max: 120, value: form.age, onChange: handleChange }), errors.age && _jsx("div", { style: errStyle, children: errors.age })] }), _jsxs("div", { style: { flex: 1 }, children: [_jsx("label", { style: labelStyle, children: "Sex" }), _jsxs("select", { style: { ...inputStyle, background: '#fff' }, name: "sex", value: form.sex, onChange: handleChange, children: [_jsx("option", { value: "", children: "Select..." }), _jsx("option", { value: "Male", children: "Male" }), _jsx("option", { value: "Female", children: "Female" }), _jsx("option", { value: "Other", children: "Other" })] }), errors.sex && _jsx("div", { style: errStyle, children: errors.sex })] })] })] })), _jsxs("div", { style: fieldWrap, children: [_jsx("label", { style: labelStyle, children: "Password" }), _jsx("input", { style: inputStyle, type: "password", name: "password", placeholder: "Min. 6 characters", value: form.password, onChange: handleChange }), errors.password && _jsx("div", { style: errStyle, children: errors.password })] }), globalErr && (_jsx("div", { style: { ...errStyle, background: '#ffeef0', padding: '8px 12px', borderRadius: 6, marginBottom: 12 }, children: globalErr })), _jsx("button", { type: "submit", disabled: submitting, style: {
                                width: '100%', padding: '10px', background: submitting ? '#888' : '#1976d2',
                                color: '#fff', border: 'none', borderRadius: 6, fontSize: 15,
                                fontWeight: 600, cursor: submitting ? 'not-allowed' : 'pointer', marginTop: 4,
                            }, children: submitting ? 'Please wait…' : isLogin ? 'Login' : 'Register' })] }), _jsxs("p", { style: { marginTop: 20, textAlign: 'center', fontSize: 13, color: '#555' }, children: [isLogin ? "Don't have an account? " : 'Already have an account? ', _jsx("button", { onClick: () => { setIsLogin(v => !v); setErrors({}); setGlobalErr(''); }, style: { background: 'none', border: 'none', color: '#1976d2', cursor: 'pointer', fontWeight: 600, fontSize: 13 }, children: isLogin ? 'Register' : 'Login' })] })] }) }));
};
export default AuthPage;
