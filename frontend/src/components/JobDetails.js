import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FiArrowLeft, FiDownload, FiEye, FiEdit, FiClock, FiCheckCircle,
  FiXCircle, FiAlertCircle, FiFileText, FiHeadphones, FiVideo,
  FiImage, FiGlobe, FiUser, FiCalendar, FiSettings, FiActivity
} from 'react-icons/fi';

const JobDetails = ({ jobId, token, onBack, onEdit }) => {
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchJobDetails();
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/jobs/${jobId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch job details: ${response.statusText}`);
      }

      const data = await response.json();
      setJob(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch job details');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status.toLowerCase()) {
      case 'completed': return <FiCheckCircle className="text-green-500" />;
      case 'failed': return <FiXCircle className="text-red-500" />;
      case 'review': return <FiAlertCircle className="text-yellow-500" />;
      default: return <FiClock className="text-blue-500" />;
    }
  };

  const getFileIcon = (mediaType) => {
    switch (mediaType) {
      case 'audio': return <FiHeadphones className="text-purple-500" />;
      case 'video': return <FiVideo className="text-red-500" />;
      case 'image': return <FiImage className="text-green-500" />;
      default: return <FiFileText className="text-blue-500" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const downloadArtifact = async (artifact) => {
    try {
      const response = await fetch(`/api/v1/jobs/${jobId}/artifacts/${artifact.id}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${artifact.artifactType}-${artifact.languageCode || 'result'}.${artifact.artifactType === 'subtitle' ? 'srt' : 'json'}`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <FiXCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error loading job</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={fetchJobDetails}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
            <button
              onClick={onBack}
              className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Go Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: FiEye },
    { id: 'files', name: 'Files', icon: FiFileText },
    { id: 'artifacts', name: 'Results', icon: FiDownload },
    { id: 'activity', name: 'Activity', icon: FiActivity },
    { id: 'settings', name: 'Settings', icon: FiSettings }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <FiArrowLeft className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{job.projectCode}</h1>
                {job.title && <p className="text-gray-600">{job.title}</p>}
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(job.status)}
                <span className="text-sm font-medium text-gray-700 capitalize">{job.status}</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {onEdit && (
                <button
                  onClick={() => onEdit(job.id)}
                  className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 flex items-center gap-2"
                >
                  <FiEdit className="h-4 w-4" />
                  Edit
                </button>
              )}
              {job.status === 'completed' && (
                <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2">
                  <FiDownload className="h-4 w-4" />
                  Download All
                </button>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="mt-6">
            <nav className="flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === 'overview' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid gap-6 lg:grid-cols-3"
          >
            {/* Job Info */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Information</h2>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex items-center gap-3">
                    <FiUser className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Created by</p>
                      <p className="font-medium">{job.createdBy}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <FiCalendar className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Created</p>
                      <p className="font-medium">{formatDate(job.createdAt)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <FiGlobe className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Languages</p>
                      <p className="font-medium">{job.sourceLanguage} → {job.targetLanguages.join(', ')}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <FiSettings className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Style</p>
                      <p className="font-medium capitalize">{job.translationStyle}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Files</span>
                    <span className="font-medium">{job.files?.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Target Languages</span>
                    <span className="font-medium">{job.targetLanguages?.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Artifacts</span>
                    <span className="font-medium">{job.artifacts?.length || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Priority</span>
                    <span className="font-medium capitalize">{job.priority}</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'files' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Files ({job.files?.length || 0})</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {job.files && job.files.length > 0 ? (
                job.files.map((file) => (
                  <div key={file.id} className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {getFileIcon(file.mediaType)}
                      <div>
                        <p className="font-medium text-gray-900">{file.originalName}</p>
                        <div className="flex items-center gap-4 mt-1">
                          <span className="text-sm text-gray-500">{formatFileSize(file.fileSize)}</span>
                          <span className="text-sm text-gray-500">{file.mimeType}</span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            file.status === 'completed' ? 'bg-green-100 text-green-800' :
                            file.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {file.status}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatDate(file.uploadedAt)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <FiFileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-600">No files found</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === 'artifacts' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Results & Artifacts ({job.artifacts?.length || 0})</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {job.artifacts && job.artifacts.length > 0 ? (
                job.artifacts.map((artifact) => (
                  <div key={artifact.id} className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <FiFileText className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="font-medium text-gray-900 capitalize">{artifact.artifactType}</p>
                        <div className="flex items-center gap-4 mt-1">
                          {artifact.languageCode && (
                            <span className="text-sm text-gray-500">Language: {artifact.languageCode}</span>
                          )}
                          {artifact.fileSize && (
                            <span className="text-sm text-gray-500">{formatFileSize(artifact.fileSize)}</span>
                          )}
                          <span className="text-sm text-gray-500">{formatDate(artifact.createdAt)}</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => downloadArtifact(artifact)}
                      className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                    >
                      <FiDownload className="h-4 w-4" />
                      Download
                    </button>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <FiFileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-600">No artifacts available yet</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === 'activity' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200"
          >
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Activity Log ({job.events?.length || 0})</h2>
            </div>
            <div className="divide-y divide-gray-200">
              {job.events && job.events.length > 0 ? (
                job.events.map((event) => (
                  <div key={event.id} className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="mt-0.5">
                        <FiActivity className="h-4 w-4 text-blue-500" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-gray-900">{event.message}</p>
                        <div className="mt-1 flex items-center gap-2">
                          <span className="text-xs text-gray-500 capitalize">{event.eventType.replace('_', ' ')}</span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">{formatDate(event.createdAt)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-12 text-center">
                  <FiActivity className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <p className="text-gray-600">No activity recorded yet</p>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {activeTab === 'settings' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Settings</h2>
            <div className="space-y-4">
              {job.settings && Object.keys(job.settings).length > 0 ? (
                Object.entries(job.settings).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                    <span className="text-sm font-medium text-gray-900">
                      {typeof value === 'boolean' ? (value ? 'Yes' : 'No') :
                       Array.isArray(value) ? value.join(', ') :
                       String(value)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-600 text-center py-8">No custom settings configured</p>
              )}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default JobDetails;