import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import JobDashboard from '../components/JobDashboard';
import JobCreate from '../components/JobCreate';
import JobDetails from '../components/JobDetails';

const JobsManager = ({ token }) => {
  const [currentView, setCurrentView] = useState('dashboard'); // dashboard, create, details
  const [selectedJobId, setSelectedJobId] = useState(null);

  const handleCreateJob = () => {
    setCurrentView('create');
  };

  const handleJobCreated = (jobId) => {
    setSelectedJobId(jobId);
    setCurrentView('details');
  };

  const handleViewJob = (jobId) => {
    setSelectedJobId(jobId);
    setCurrentView('details');
  };

  const handleBack = () => {
    setCurrentView('dashboard');
    setSelectedJobId(null);
  };

  const handleEditJob = (jobId) => {
    // For now, just redirect to create - in future could be edit mode
    setCurrentView('create');
  };

  return (
    <div className="min-h-screen">
      <AnimatePresence mode="wait">
        {currentView === 'dashboard' && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            <JobDashboard
              token={token}
              onCreateJob={handleCreateJob}
              onViewJob={handleViewJob}
            />
          </motion.div>
        )}

        {currentView === 'create' && (
          <motion.div
            key="create"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="relative">
              <button
                onClick={handleBack}
                className="fixed top-6 left-6 z-10 bg-white shadow-md rounded-lg px-4 py-2 text-gray-700 hover:bg-gray-50 flex items-center gap-2 border"
              >
                ← Back to Jobs
              </button>
              <JobCreate
                token={token}
                onJobCreated={handleJobCreated}
              />
            </div>
          </motion.div>
        )}

        {currentView === 'details' && selectedJobId && (
          <motion.div
            key="details"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <JobDetails
              jobId={selectedJobId}
              token={token}
              onBack={handleBack}
              onEdit={handleEditJob}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default JobsManager;