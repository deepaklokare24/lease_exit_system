import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { Box, CircularProgress } from '@mui/material';
import Layout from './components/Layout';

// Lazy load pages for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const LeaseExitForm = lazy(() => import('./pages/LeaseExitForm'));
const LeaseExitDetails = lazy(() => import('./pages/LeaseExitDetails'));
const ApprovalPage = lazy(() => import('./pages/ApprovalPage'));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'));

// Loading component for suspense fallback
const LoadingFallback = () => (
  <Box
    display="flex"
    justifyContent="center"
    alignItems="center"
    minHeight="100vh"
  >
    <CircularProgress />
  </Box>
);

function App() {
  return (
    <>
      <ToastContainer position="top-right" autoClose={5000} />
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="lease-exit-form" element={<LeaseExitForm />} />
            <Route path="lease-exit/:id" element={<LeaseExitDetails />} />
            <Route path="approvals" element={<ApprovalPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </>
  );
}

export default App; 