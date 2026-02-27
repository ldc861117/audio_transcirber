import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import Dashboard from './pages/Dashboard/Dashboard';
import Transcribe from './pages/Transcribe/Transcribe';
import History from './pages/History/History';
import Speakers from './pages/Speakers/Speakers';
import Settings from './pages/Settings/Settings';
import Login from './pages/Login/Login';
import Register from './pages/Login/Register';
import { useAuthStore } from './stores/authStore';
import './styles/global.css';

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout><Dashboard /></Layout>} path="/" />
          <Route element={<Layout><Transcribe /></Layout>} path="/transcribe" />
          <Route element={<Layout><History /></Layout>} path="/history" />
          <Route element={<Layout><Speakers /></Layout>} path="/speakers" />
          <Route element={<Layout><Settings /></Layout>} path="/settings" />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
