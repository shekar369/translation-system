import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
  Download,
  FileText,
  Globe,
  Calendar,
  BarChart3,
  Trash2,
  RefreshCw,
  Play
} from 'lucide-react';
import toast from 'react-hot-toast';

const statusConfig = {
  pending: {
    icon: Clock,
    color: 'text-yellow-600',
    bg: 'bg-yellow-100',
    border: 'border-yellow-200',
    label: 'Pending',
    progress: 0
  },
  processing: {
    icon: Loader,
    color: 'text-blue-600',
    bg: 'bg-blue-100',
    border: 'border-blue-200',
    label: 'Processing',
    progress: 50
  },
  completed: {
    icon: CheckCircle,
    color: 'text-green-600',
    bg: 'bg-green-100',
    border: 'border-green-200',
    label: 'Completed',
    progress: 100
  },
  failed: {
    icon: AlertCircle,
    color: 'text-red-600',
    bg: 'bg-red-100',
    border: 'border-red-200',
    label: 'Failed',
    progress: 0
  }
};

const languages = {
  'en': 'English',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'it': 'Italian',
  'pt': 'Portuguese',
  'ru': 'Russian',
  'ja': 'Japanese',
  'ko': 'Korean',
  'zh': 'Chinese',
  'ar': 'Arabic',
  'hi': 'Hindi'
};

function TranslationJobs({ token, jobs, setJobs, refreshTrigger }) {
  const [loading, setLoading] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState([]);

  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/translate/jobs', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setJobs(data);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      toast.error('Failed to fetch translation jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (jobId) => {
    try {
      const response = await fetch(`/api/translate/jobs/${jobId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `translation-${jobId}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success('Download started!');
      } else {
        toast.error('Download failed');
      }
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Download failed');
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this translation job?')) return;

    try {
      const response = await fetch(`/api/translate/jobs/${jobId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setJobs(jobs.filter(job => job.id !== jobId));
        toast.success('Job deleted successfully');
      } else {
        toast.error('Failed to delete job');
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Failed to delete job');
    }
  };

  const handleProcess = async (jobId) => {
    if (!window.confirm('Process this translation job now?')) return;

    try {
      const response = await fetch(`/api/translate/jobs/${jobId}/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'completed') {
          toast.success('Translation completed successfully!');
          fetchJobs(); // Refresh the jobs list
        } else if (result.status === 'failed') {
          toast.error(`Translation failed: ${result.error}`);
        } else {
          toast.success(result.message || 'Job processing started');
        }
      } else {
        toast.error('Failed to process job');
      }
    } catch (error) {
      console.error('Process error:', error);
      toast.error('Failed to process job');
    }
  };

  const getStatusStats = () => {
    const stats = {
      total: jobs.length,
      pending: jobs.filter(j => j.status === 'pending').length,
      processing: jobs.filter(j => j.status === 'processing').length,
      completed: jobs.filter(j => j.status === 'completed').length,
      failed: jobs.filter(j => j.status === 'failed').length,
    };
    return stats;
  };

  const stats = getStatusStats();

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Loading translation jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Translation Jobs</h2>
          <p className="text-gray-600">Monitor and manage your translation progress</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={fetchJobs}
          disabled={loading}
          className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </motion.button>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-4"
      >
        {[
          { label: 'Total', value: stats.total, color: 'from-gray-500 to-gray-600', icon: BarChart3 },
          { label: 'Pending', value: stats.pending, color: 'from-yellow-500 to-orange-500', icon: Clock },
          { label: 'Processing', value: stats.processing, color: 'from-blue-500 to-indigo-500', icon: Loader },
          { label: 'Completed', value: stats.completed, color: 'from-green-500 to-emerald-500', icon: CheckCircle },
          { label: 'Failed', value: stats.failed, color: 'from-red-500 to-pink-500', icon: AlertCircle }
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl p-6 shadow-lg border border-gray-200/50 hover-lift"
            >
              <div className="flex items-center space-x-3">
                <div className={`bg-gradient-to-r ${stat.color} p-2 rounded-xl`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-sm text-gray-600">{stat.label}</p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Jobs List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50"
      >
        <div className="p-6 border-b border-gray-200/50">
          <h3 className="text-xl font-bold text-gray-900">Recent Jobs</h3>
        </div>

        {jobs.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
            <p className="text-gray-600">No translation jobs yet.</p>
            <p className="text-sm text-gray-500 mt-1">Start by uploading a document!</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200/50">
            <AnimatePresence>
              {jobs.map((job, index) => {
                const config = statusConfig[job.status] || statusConfig.pending;
                const Icon = config.icon;

                return (
                  <motion.div
                    key={job.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className="p-6 hover:bg-gray-50/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 flex-1">
                        {/* Status indicator */}
                        <div className={`p-2 rounded-xl ${config.bg} ${config.border} border`}>
                          <Icon className={`w-5 h-5 ${config.color} ${
                            job.status === 'processing' ? 'animate-spin' : ''
                          }`} />
                        </div>

                        {/* Job details */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3 mb-1">
                            <h4 className="text-lg font-semibold text-gray-900 truncate">
                              Job #{job.id}
                            </h4>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
                              {config.label}
                            </span>
                          </div>

                          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
                            <div className="flex items-center space-x-1">
                              <Globe className="w-4 h-4" />
                              <span>{languages[job.source_language]} → {languages[job.target_language]}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Calendar className="w-4 h-4" />
                              <span>{new Date(job.created_at).toLocaleDateString()}</span>
                            </div>
                          </div>

                          {/* Progress bar */}
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                            <motion.div
                              className={`h-2 rounded-full ${
                                job.status === 'completed' ? 'bg-green-500' :
                                job.status === 'processing' ? 'bg-blue-500' :
                                job.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                              }`}
                              initial={{ width: 0 }}
                              animate={{ width: `${config.progress}%` }}
                              transition={{ duration: 1, delay: index * 0.1 }}
                            />
                          </div>

                          {job.error_message && (
                            <p className="text-sm text-red-600 mt-1">{job.error_message}</p>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-2 ml-4">
                        {job.status === 'pending' && (
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleProcess(job.id)}
                            className="flex items-center space-x-1 bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                          >
                            <Play className="w-4 h-4" />
                            <span>Process</span>
                          </motion.button>
                        )}

                        {job.status === 'completed' && (
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleDownload(job.id)}
                            className="flex items-center space-x-1 bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            <span>Download</span>
                          </motion.button>
                        )}

                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleDelete(job.id)}
                          className="flex items-center space-x-1 bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                          <span>Delete</span>
                        </motion.button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </motion.div>
    </div>
  );
}

export default TranslationJobs;