import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Settings,
  Globe,
  Play,
  X,
  Plus,
  AlertCircle,
  CheckCircle,
  Clock,
  Languages
} from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

interface FileUpload {
  file: File;
  id: string;
  progress: number;
  status: 'pending' | 'uploading' | 'uploaded' | 'error';
  objectKey?: string;
  checksum?: string;
  mediaType?: string;
}

interface JobSettings {
  translationStyle: 'formal' | 'neutral' | 'casual';
  glossaryId?: string;
  subtitleOptions: {
    mode: 'burn' | 'sidecar';
    maxCharsPerLine: number;
    maxLines: number;
    readingSpeedWpm: number;
  };
  tts: {
    mode: 'none' | 'generate_dub' | 'generate_audio_subtrack';
    voice?: string;
  };
  deliveryFormats: string[];
  privacy: 'on-prem_only' | 'allow_cloud';
  humanReview: boolean;
}

const defaultSettings: JobSettings = {
  translationStyle: 'neutral',
  subtitleOptions: {
    mode: 'sidecar',
    maxCharsPerLine: 42,
    maxLines: 2,
    readingSpeedWpm: 160,
  },
  tts: {
    mode: 'none',
  },
  deliveryFormats: ['rebuild_original'],
  privacy: 'allow_cloud',
  humanReview: false,
};

const languages = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  it: 'Italian',
  pt: 'Portuguese',
  ru: 'Russian',
  ja: 'Japanese',
  ko: 'Korean',
  zh: 'Chinese',
  ar: 'Arabic',
  hi: 'Hindi',
};

const JobCreate: React.FC<{ token: string; onJobCreated: (jobId: string) => void }> = ({
  token,
  onJobCreated,
}) => {
  // Form state
  const [projectCode, setProjectCode] = useState('CS101-2025');
  const [title, setTitle] = useState('CS101-2025 - Full course materials translation EN->ES');
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [targetLanguages, setTargetLanguages] = useState(['es']);
  const [priority, setPriority] = useState<'normal' | 'fast' | 'immediate'>('normal');

  // File upload state
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Modal state
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState<JobSettings>(defaultSettings);

  // Job creation state
  const [isCreating, setIsCreating] = useState(false);

  // File upload with dropzone
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const newFiles = acceptedFiles.map((file) => ({
        file,
        id: Math.random().toString(36).substring(7),
        progress: 0,
        status: 'pending' as const,
      }));

      setFiles((prev) => [...prev, ...newFiles]);
    },
    []
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
      'video/mp4': ['.mp4'],
    },
    maxSize: 2000 * 1024 * 1024, // 2GB max
    multiple: true,
  });

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const uploadFiles = async () => {
    setIsUploading(true);

    try {
      for (const fileUpload of files) {
        if (fileUpload.status === 'uploaded') continue;

        // Update status
        setFiles((prev) =>
          prev.map((f) => (f.id === fileUpload.id ? { ...f, status: 'uploading' } : f))
        );

        // Generate presigned URL
        const presignedResponse = await fetch('/api/v1/files/presigned-url', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            filename: fileUpload.file.name,
            contentType: fileUpload.file.type,
            size: fileUpload.file.size,
          }),
        });

        if (!presignedResponse.ok) {
          throw new Error(`Failed to get presigned URL: ${presignedResponse.statusText}`);
        }

        const { uploadUrl, objectKey } = await presignedResponse.json();

        // Upload file directly to MinIO
        const uploadResponse = await fetch(uploadUrl, {
          method: 'PUT',
          body: fileUpload.file,
          headers: {
            'Content-Type': fileUpload.file.type,
          },
        });

        if (!uploadResponse.ok) {
          throw new Error(`Upload failed: ${uploadResponse.statusText}`);
        }

        // Calculate checksum and determine media type
        const checksum = await calculateChecksum(fileUpload.file);
        const mediaType = getMediaType(fileUpload.file.type);

        // Update file status
        setFiles((prev) =>
          prev.map((f) =>
            f.id === fileUpload.id
              ? {
                  ...f,
                  status: 'uploaded',
                  objectKey,
                  checksum,
                  mediaType,
                  progress: 100,
                }
              : f
          )
        );
      }

      toast.success('All files uploaded successfully!');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  };

  const createJob = async () => {
    // Validate form
    if (!projectCode.trim()) {
      toast.error('Project code is required');
      return;
    }

    if (files.length === 0) {
      toast.error('Please upload at least one file');
      return;
    }

    if (targetLanguages.length === 0) {
      toast.error('Please select at least one target language');
      return;
    }

    // Check if all files are uploaded
    const uploadedFiles = files.filter((f) => f.status === 'uploaded');
    if (uploadedFiles.length !== files.length) {
      toast.error('Please upload all files before creating the job');
      return;
    }

    setIsCreating(true);

    try {
      const jobData = {
        projectCode: projectCode.trim(),
        title: title.trim() || `${projectCode.trim()} - Translation Project`,
        sourceLanguage,
        targetLanguages,
        priority,
        settings,
        files: uploadedFiles.map((f) => ({
          filename: f.file.name,
          objectKey: f.objectKey!,
          mimeType: f.file.type,
          size: f.file.size,
          checksum: f.checksum!,
          mediaType: f.mediaType!,
          pages: f.mediaType === 'document' ? 1 : undefined, // Mock
          durationSeconds: f.mediaType === 'audio' || f.mediaType === 'video' ? 120 : undefined, // Mock
        })),
      };

      const response = await fetch('/api/v1/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(jobData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create job');
      }

      const result = await response.json();
      toast.success(`Job created successfully! ID: ${result.id}`);
      onJobCreated(result.id);

      // Reset form
      setProjectCode('');
      setTitle('');
      setFiles([]);
      setSettings(defaultSettings);
    } catch (error) {
      console.error('Job creation error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to create job');
    } finally {
      setIsCreating(false);
    }
  };

  const addTargetLanguage = (langCode: string) => {
    if (!targetLanguages.includes(langCode) && langCode !== sourceLanguage) {
      setTargetLanguages([...targetLanguages, langCode]);
    }
  };

  const removeTargetLanguage = (langCode: string) => {
    setTargetLanguages(targetLanguages.filter((l) => l !== langCode));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Translation Job</h1>
        <p className="text-gray-600">Upload course materials and configure translation settings</p>
      </motion.div>

      {/* Basic Information */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white rounded-2xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2 text-primary-500" />
          Project Information
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project Code *
            </label>
            <input
              type="text"
              value={projectCode}
              onChange={(e) => setProjectCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="e.g., CS101-2025"
              maxLength={100}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="normal">Normal</option>
              <option value="fast">Fast</option>
              <option value="immediate">Immediate</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Project Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Optional: Custom title for this project"
            />
          </div>
        </div>
      </motion.div>

      {/* Language Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white rounded-2xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Languages className="w-5 h-5 mr-2 text-primary-500" />
          Language Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Source Language
            </label>
            <select
              value={sourceLanguage}
              onChange={(e) => {
                setSourceLanguage(e.target.value);
                // Remove from target languages if selected
                setTargetLanguages(targetLanguages.filter((l) => l !== e.target.value));
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {Object.entries(languages).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Languages *
            </label>
            <div className="space-y-2">
              <div className="flex flex-wrap gap-2 min-h-[2.5rem] p-2 border border-gray-300 rounded-lg">
                {targetLanguages.map((langCode) => (
                  <span
                    key={langCode}
                    className="inline-flex items-center px-2 py-1 bg-primary-100 text-primary-800 text-sm rounded-md"
                  >
                    {languages[langCode as keyof typeof languages]}
                    <button
                      onClick={() => removeTargetLanguage(langCode)}
                      className="ml-1 text-primary-600 hover:text-primary-800"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    addTargetLanguage(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">Add target language...</option>
                {Object.entries(languages)
                  .filter(([code]) => code !== sourceLanguage && !targetLanguages.includes(code))
                  .map(([code, name]) => (
                    <option key={code} value={code}>
                      {name}
                    </option>
                  ))}
              </select>
            </div>
          </div>
        </div>
      </motion.div>

      {/* File Upload */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-2xl shadow-lg p-6"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Upload className="w-5 h-5 mr-2 text-primary-500" />
          File Upload
        </h2>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
          </p>
          <p className="text-gray-500 mb-4">
            or{' '}
            <span className="text-primary-500 font-medium cursor-pointer">browse files</span>
          </p>
          <p className="text-sm text-gray-400">
            Supported: PDF, DOCX, PPTX, TXT, MP3, WAV, MP4 (max 2GB each)
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-6 space-y-2">
            <h3 className="font-medium text-gray-900">Uploaded Files ({files.length})</h3>
            {files.map((fileUpload) => (
              <div
                key={fileUpload.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    {fileUpload.status === 'uploaded' ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : fileUpload.status === 'uploading' ? (
                      <Clock className="w-5 h-5 text-blue-500" />
                    ) : fileUpload.status === 'error' ? (
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    ) : (
                      <FileText className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{fileUpload.file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(fileUpload.file.size / (1024 * 1024)).toFixed(1)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(fileUpload.id)}
                  className="text-red-500 hover:text-red-700"
                  disabled={isUploading}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}

            {files.some((f) => f.status !== 'uploaded') && (
              <button
                onClick={uploadFiles}
                disabled={isUploading}
                className="w-full mt-4 bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {isUploading ? 'Uploading...' : 'Upload Files'}
              </button>
            )}
          </div>
        )}
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="flex items-center justify-between"
      >
        <button
          onClick={() => setShowSettingsModal(true)}
          className="flex items-center space-x-2 bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-xl font-medium transition-colors"
        >
          <Settings className="w-4 h-4" />
          <span>Advanced Settings</span>
        </button>

        <button
          onClick={createJob}
          disabled={isCreating || files.length === 0 || files.some((f) => f.status !== 'uploaded')}
          className="flex items-center space-x-2 bg-primary-500 hover:bg-primary-600 text-white px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreating ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          <span>{isCreating ? 'Creating...' : 'Create & Start Job'}</span>
        </button>
      </motion.div>

      {/* Settings Modal */}
      <AnimatePresence>
        {showSettingsModal && (
          <SettingsModal
            settings={settings}
            onSettingsChange={setSettings}
            onClose={() => setShowSettingsModal(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

// Helper functions
const calculateChecksum = async (file: File): Promise<string> => {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
};

const getMediaType = (mimeType: string): string => {
  if (mimeType.startsWith('audio/')) return 'audio';
  if (mimeType.startsWith('video/')) return 'video';
  if (mimeType.startsWith('image/')) return 'image';
  return 'document';
};

// Settings Modal Component
const SettingsModal: React.FC<{
  settings: JobSettings;
  onSettingsChange: (settings: JobSettings) => void;
  onClose: () => void;
}> = ({ settings, onSettingsChange, onClose }) => {
  const updateSettings = (updates: Partial<JobSettings>) => {
    onSettingsChange({ ...settings, ...updates });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold text-gray-900">Advanced Settings</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Translation Style */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Translation Style
            </label>
            <select
              value={settings.translationStyle}
              onChange={(e) =>
                updateSettings({
                  translationStyle: e.target.value as 'formal' | 'neutral' | 'casual',
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="formal">Formal</option>
              <option value="neutral">Neutral</option>
              <option value="casual">Casual</option>
            </select>
          </div>

          {/* Privacy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Privacy Mode
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="privacy"
                  value="allow_cloud"
                  checked={settings.privacy === 'allow_cloud'}
                  onChange={(e) => updateSettings({ privacy: e.target.value as any })}
                  className="mr-2"
                />
                Allow cloud services (faster, more languages)
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="privacy"
                  value="on-prem_only"
                  checked={settings.privacy === 'on-prem_only'}
                  onChange={(e) => updateSettings({ privacy: e.target.value as any })}
                  className="mr-2"
                />
                On-premises only (secure, private)
              </label>
            </div>
          </div>

          {/* Delivery Formats */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Delivery Formats
            </label>
            <div className="space-y-2">
              {[
                { id: 'rebuild_original', label: 'Rebuild original format (PDF/DOCX/PPTX)' },
                { id: 'html', label: 'HTML format' },
                { id: 'markdown', label: 'Markdown format' },
                { id: 'subtitles', label: 'Subtitle files (SRT/VTT)' },
                { id: 'transcripts', label: 'Transcript files' },
              ].map((format) => (
                <label key={format.id} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.deliveryFormats.includes(format.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        updateSettings({
                          deliveryFormats: [...settings.deliveryFormats, format.id],
                        });
                      } else {
                        updateSettings({
                          deliveryFormats: settings.deliveryFormats.filter(
                            (f) => f !== format.id
                          ),
                        });
                      }
                    }}
                    className="mr-2"
                  />
                  {format.label}
                </label>
              ))}
            </div>
          </div>

          {/* Human Review */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={settings.humanReview}
                onChange={(e) => updateSettings({ humanReview: e.target.checked })}
                className="mr-2"
              />
              Require human review before finalization
            </label>
          </div>
        </div>

        <div className="p-6 border-t flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Save Settings
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default JobCreate;