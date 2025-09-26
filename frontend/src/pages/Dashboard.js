import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, Search, Menu, X } from 'lucide-react';
import { Toaster } from 'react-hot-toast';
import Sidebar from '../components/Sidebar';
import FileUpload from '../components/FileUpload';
import TranslationJobs from '../components/TranslationJobs';
import DocumentList from '../components/DocumentList';
import Support from './Support';
import JobsManager from './JobsManager';

function Dashboard({ token, user, onLogout }) {
  const [activeTab, setActiveTab] = useState('upload');
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const refresh = () => setRefreshTrigger(prev => prev + 1);

  // Close mobile menu when tab changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [activeTab]);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'upload': return 'Upload & Translate';
      case 'documents': return 'My Documents';
      case 'jobs': return 'Job-based Translation System';
      case 'jobs-legacy': return 'Translation Jobs (Legacy)';
      case 'support': return 'Documentation & Support';
      case 'analytics': return 'Analytics Dashboard';
      case 'settings': return 'Settings';
      default: return 'Dashboard';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-secondary-50 via-white to-primary-50">
      <Toaster position="top-right" />

      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onLogout={onLogout}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Mobile menu overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Main content */}
      <div className={`transition-all duration-300 ${sidebarCollapsed ? 'ml-20' : 'ml-72'}`}>
        {/* Top bar */}
        <motion.header
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 sticky top-0 z-20"
        >
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {/* Mobile menu button */}
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                </button>

                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{getPageTitle()}</h1>
                  <p className="text-sm text-gray-600">Manage your translations with ease</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Search bar */}
                <div className="relative hidden md:block">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search documents..."
                    className="pl-10 pr-4 py-2 bg-gray-100 border-0 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition-all w-64"
                  />
                </div>

                {/* Notifications */}
                <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
                  <Bell className="w-5 h-5 text-gray-600" />
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
                </button>

                {/* User profile */}
                <div className="flex items-center space-x-3">
                  <div className="hidden sm:block text-right">
                    <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                    <p className="text-xs text-gray-600">Premium Plan</p>
                  </div>
                  <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold text-sm">
                      {user?.email?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.header>

        {/* Page content */}
        <main className="p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === 'upload' && (
                <FileUpload token={token} onSuccess={refresh} />
              )}
              {activeTab === 'documents' && (
                <DocumentList
                  token={token}
                  documents={documents}
                  setDocuments={setDocuments}
                  refreshTrigger={refreshTrigger}
                />
              )}
              {activeTab === 'jobs' && (
                <JobsManager token={token} />
              )}
              {activeTab === 'jobs-legacy' && (
                <TranslationJobs
                  token={token}
                  jobs={jobs}
                  setJobs={setJobs}
                  refreshTrigger={refreshTrigger}
                />
              )}
              {activeTab === 'support' && (
                <Support token={token} />
              )}
              {activeTab === 'analytics' && (
                <div className="bg-white rounded-2xl p-8 shadow-lg">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Analytics Dashboard</h3>
                  <p className="text-gray-600">Analytics features coming soon...</p>
                </div>
              )}
              {activeTab === 'settings' && (
                <div className="bg-white rounded-2xl p-8 shadow-lg">
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Settings</h3>
                  <p className="text-gray-600">Settings panel coming soon...</p>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;