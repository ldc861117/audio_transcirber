import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import Layout from './components/Layout/Layout';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import Dashboard from './pages/Dashboard/Dashboard';
import Transcribe from './pages/Transcribe/Transcribe';
import History from './pages/History/History';
import Speakers from './pages/Speakers/Speakers';
import Settings from './pages/Settings/Settings';
import Pricing from './pages/Pricing/Pricing';
import Account from './pages/Account/Account';
import Login from './pages/Login/Login';
import Register from './pages/Login/Register';
import { useAuthStore } from './stores/authStore';
import './styles/global.css';

const PageWrapper = ({ children }) => (
  <Motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.2, ease: "easeOut" }}
  >
    {children}
  </Motion.div>
);

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/pricing" element={<Layout><PageWrapper><Pricing /></PageWrapper></Layout>} />

        <Route element={<ProtectedRoute />}>
          <Route element={<Layout><PageWrapper><Dashboard /></PageWrapper></Layout>} path="/" />
          <Route element={<Layout><PageWrapper><Transcribe /></PageWrapper></Layout>} path="/transcribe" />
          <Route element={<Layout><PageWrapper><History /></PageWrapper></Layout>} path="/history" />
          <Route element={<Layout><PageWrapper><Speakers /></PageWrapper></Layout>} path="/speakers" />
          <Route element={<Layout><PageWrapper><Settings /></PageWrapper></Layout>} path="/settings" />
          <Route element={<Layout><PageWrapper><Account /></PageWrapper></Layout>} path="/account" />
        </Route>
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Router>
      <AnimatedRoutes />
    </Router>
  );
}

export default App;
