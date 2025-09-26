import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import {
  FiUpload, FiX, FiFile, FiSettings, FiCheck,
  FiAlertCircle, FiPlus, FiMinus
} from 'react-icons/fi';
import toast from 'react-hot-toast';

const JobCreate = ({ token, onJobCreated }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [projectCode, setProjectCode] = useState('CS101-2025');
  const [title, setTitle] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguages, setTargetLanguages] = useState(['es']);
  const [priority, setPriority] = useState('normal');
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [settings, setSettings] = useState({
    translationStyle: 'neutral',
    humanReview: false,
    privacy: 'allow_cloud',
    deliveryFormats: ['original'],
    preserveFormatting: true,
    glossaryId: null
  });

  const languages = [
    { code: 'auto', name: 'Auto-detect' },
    { code: 'en', name: 'English' },
    { code: 'es', name: 'Spanish' },
    { code: 'fr', name: 'French' },
    { code: 'de', name: 'German' },
    { code: 'it', name: 'Italian' },
    { code: 'pt', name: 'Portuguese' },
    { code: 'ru', name: 'Russian' },
    { code: 'ja', name: 'Japanese' },
    { code: 'ko', name: 'Korean' },
    { code: 'zh', name: 'Chinese' },
    { code: 'ar', name: 'Arabic' },
    { code: 'hi', name: 'Hindi' },
    { code: 'th', name: 'Thai' },
    { code: 'vi', name: 'Vietnamese' }
  ];

  const onDrop = async (acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      uploading: false,
      uploaded: false,
      objectKey: null,
      error: null
    }));

    setFiles(prev => [...prev, ...newFiles]);

    // Start uploading files
    for (let fileUpload of newFiles) {
      await uploadFile(fileUpload);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'audio/*': ['.mp3', '.wav', '.m4a', '.ogg'],
      'video/*': ['.mp4', '.mov', '.avi', '.mkv']
    },
    maxSize: 100 * 1024 * 1024 // 100MB
  });

  const uploadFile = async (fileUpload) => {
    try {
      // Update file state to uploading
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? { ...f, uploading: true } : f
      ));

      // Get presigned URL
      const urlResponse = await fetch('/api/v1/files/upload-url', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          filename: fileUpload.file.name,
          contentType: fileUpload.file.type
        })
      });

      if (!urlResponse.ok) {
        throw new Error('Failed to get upload URL');
      }

      const { uploadUrl, objectKey } = await urlResponse.json();

      // Upload file to MinIO
      const uploadResponse = await fetch(uploadUrl, {
        method: 'PUT',
        body: fileUpload.file,
        headers: {
          'Content-Type': fileUpload.file.type
        }
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload file');
      }

      // Update file state to uploaded
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? {
          ...f,
          uploading: false,
          uploaded: true,
          objectKey: objectKey
        } : f
      ));

    } catch (error) {
      console.error('Upload error:', error);
      setFiles(prev => prev.map(f =>
        f.id === fileUpload.id ? {
          ...f,
          uploading: false,
          error: error.message
        } : f
      ));
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const addTargetLanguage = () => {
    const availableLanguages = languages
      .filter(lang => lang.code !== 'auto' && !targetLanguages.includes(lang.code))
      .map(lang => lang.code);

    if (availableLanguages.length > 0) {
      setTargetLanguages(prev => [...prev, availableLanguages[0]]);
    }
  };

  const removeTargetLanguage = (index) => {
    if (targetLanguages.length > 1) {
      setTargetLanguages(prev => prev.filter((_, i) => i !== index));
    }
  };

  const updateTargetLanguage = (index, newLang) => {
    setTargetLanguages(prev => prev.map((lang, i) => i === index ? newLang : lang));
  };

  const createJob = async () => {
    if (files.length === 0) {
      toast.error('Please upload at least one file');
      return;
    }

    const uploadedFiles = files.filter(f => f.uploaded);
    if (uploadedFiles.length === 0) {
      toast.error('Please wait for files to finish uploading');
      return;
    }

    if (!projectCode.trim()) {
      toast.error('Please enter a project code');
      return;
    }

    if (targetLanguages.length === 0) {
      toast.error('Please select at least one target language');
      return;
    }

    setUploading(true);

    try {
      const jobData = {
        projectCode: projectCode.trim(),
        title: title.trim() || null,
        sourceLanguage,
        targetLanguages,
        priority,
        settings,
        files: uploadedFiles.map(f => ({
          filename: f.file.name,
          objectKey: f.objectKey
        }))
      };

      const response = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(jobData)
      });

      if (!response.ok) {
        throw new Error(`Failed to create job: ${response.statusText}`);
      }

      const result = await response.json();
      toast.success('Translation job created successfully!');
      onJobCreated(result.id);

    } catch (error) {
      console.error('Create job error:', error);
      toast.error(error.message || 'Failed to create translation job');
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Translation Job</h1>
          <p className="text-gray-600">Upload files and configure translation settings for your project</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Project Information */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Information</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Code *
                  </label>
                  <input
                    type="text"
                    value={projectCode}
                    onChange={(e) => setProjectCode(e.target.value)}
                    placeholder="e.g., CS101-2025"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Descriptive title for this job"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low</option>
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Language Configuration */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Language Configuration</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Source Language
                  </label>
                  <select
                    value={sourceLanguage}
                    onChange={(e) => setSourceLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {languages.map(lang => (
                      <option key={lang.code} value={lang.code}>{lang.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Target Languages *
                    </label>
                    <button
                      onClick={addTargetLanguage}
                      className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                      type="button"
                    >
                      <FiPlus className="h-4 w-4" />
                      Add Language
                    </button>
                  </div>

                  <div className="space-y-2">
                    {targetLanguages.map((lang, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <select
                          value={lang}
                          onChange={(e) => updateTargetLanguage(index, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          {languages
                            .filter(l => l.code !== 'auto')
                            .map(language => (
                              <option key={language.code} value={language.code}>
                                {language.name}
                              </option>
                            ))}
                        </select>
                        {targetLanguages.length > 1 && (
                          <button
                            onClick={() => removeTargetLanguage(index)}
                            className="p-2 text-red-600 hover:text-red-800"
                            type="button"
                          >
                            <FiMinus className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* File Upload */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Files</h2>

              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                  isDragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <FiUpload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  {isDragActive ? 'Drop files here' : 'Upload your files'}
                </p>
                <p className="text-gray-600 mb-4">
                  Drag and drop files here, or click to browse
                </p>
                <p className="text-sm text-gray-500">
                  Supports: PDF, DOCX, PPTX, TXT, MP3, WAV, MP4 (max 100MB each)
                </p>
              </div>

              {files.length > 0 && (
                <div className="mt-6 space-y-2">
                  {files.map((fileUpload) => (
                    <motion.div
                      key={fileUpload.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <FiFile className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {fileUpload.file.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatFileSize(fileUpload.file.size)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {fileUpload.uploading && (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        )}
                        {fileUpload.uploaded && (
                          <FiCheck className="h-4 w-4 text-green-600" />
                        )}
                        {fileUpload.error && (
                          <FiAlertCircle className="h-4 w-4 text-red-600" />
                        )}
                        <button
                          onClick={() => removeFile(fileUpload.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
                        >
                          <FiX className="h-4 w-4" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Advanced Settings */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <button
                onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                className="w-full p-6 flex items-center justify-between text-left hover:bg-gray-50"
                type="button"
              >
                <div className="flex items-center gap-3">
                  <FiSettings className="h-5 w-5 text-gray-600" />
                  <h2 className="text-lg font-semibold text-gray-900">Advanced Settings</h2>
                </div>
                <motion.div
                  animate={{ rotate: showAdvancedSettings ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <FiPlus className="h-5 w-5 text-gray-400" />
                </motion.div>
              </button>

              {showAdvancedSettings && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="px-6 pb-6 border-t border-gray-200 space-y-4"
                >
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Translation Style
                    </label>
                    <select
                      value={settings.translationStyle}
                      onChange={(e) => setSettings(prev => ({ ...prev, translationStyle: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="neutral">Neutral</option>
                      <option value="formal">Formal</option>
                      <option value="informal">Informal</option>
                      <option value="academic">Academic</option>
                      <option value="technical">Technical</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Privacy Mode
                    </label>
                    <select
                      value={settings.privacy}
                      onChange={(e) => setSettings(prev => ({ ...prev, privacy: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="allow_cloud">Allow cloud services</option>
                      <option value="on-prem_only">On-premises only</option>
                    </select>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="humanReview"
                      checked={settings.humanReview}
                      onChange={(e) => setSettings(prev => ({ ...prev, humanReview: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="humanReview" className="ml-2 text-sm text-gray-700">
                      Require human review before completion
                    </label>
                  </div>

                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="preserveFormatting"
                      checked={settings.preserveFormatting}
                      onChange={(e) => setSettings(prev => ({ ...prev, preserveFormatting: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="preserveFormatting" className="ml-2 text-sm text-gray-700">
                      Preserve original formatting
                    </label>
                  </div>
                </motion.div>
              )}
            </div>
          </div>

          {/* Summary Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sticky top-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Summary</h2>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Project:</span>
                  <span className="font-medium">{projectCode || 'Not set'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Files:</span>
                  <span className="font-medium">{files.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Languages:</span>
                  <span className="font-medium">{targetLanguages.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Priority:</span>
                  <span className="font-medium capitalize">{priority}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Review:</span>
                  <span className="font-medium">{settings.humanReview ? 'Yes' : 'No'}</span>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-200">
                <button
                  onClick={createJob}
                  disabled={uploading || files.length === 0 || !projectCode.trim()}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Creating Job...
                    </>
                  ) : (
                    'Create Translation Job'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobCreate;