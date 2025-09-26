import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Image,
  X,
  Globe,
  ArrowRight,
  CheckCircle,
  Loader,
  AlertCircle,
  Sparkles
} from 'lucide-react';
import toast from 'react-hot-toast';

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

function FileUpload({ token, onSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [translating, setTranslating] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [sourceLang, setSourceLang] = useState('en');
  const [targetLang, setTargetLang] = useState('es');
  const [message, setMessage] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [step, setStep] = useState('upload'); // 'upload', 'configure', 'translate', 'complete'

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/rtf': ['.rtf'],
      'text/html': ['.html']
    },
    maxFiles: 1,
    onDrop: handleFileDrop
  });

  async function handleFileDrop(acceptedFiles) {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setMessage('');
    setUploadProgress(0);
    setStep('upload');

    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + Math.random() * 15;
      });
    }, 200);

    try {
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const document = await response.json();
      setUploadProgress(100);

      setTimeout(() => {
        setUploadedFile(document);
        setStep('configure');
        toast.success(`File uploaded successfully: ${document.filename}`);
        onSuccess();
      }, 500);

    } catch (error) {
      clearInterval(progressInterval);
      setMessage(`Upload error: ${error.message}`);
      toast.error(error.message);
    } finally {
      clearInterval(progressInterval);
      setTimeout(() => {
        setUploading(false);
      }, 1000);
    }
  }

  async function handleTranslate() {
    if (!uploadedFile) return;

    setTranslating(true);
    setMessage('');
    setStep('translate');

    try {
      const response = await fetch('/api/translate/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_id: uploadedFile.id,
          source_language: sourceLang,
          target_language: targetLang
        })
      });

      if (!response.ok) {
        throw new Error('Translation request failed');
      }

      const job = await response.json();
      setStep('complete');
      toast.success(`Translation started! Job ID: ${job.job_id}`);
      setMessage(`Translation job created successfully! Check the Jobs tab to monitor progress.`);
      onSuccess();
    } catch (error) {
      setMessage(`Translation error: ${error.message}`);
      toast.error(error.message);
    } finally {
      setTranslating(false);
    }
  }

  const getFileIcon = (filename) => {
    const ext = filename?.toLowerCase().split('.').pop();
    switch (ext) {
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
      case 'rtf':
      case 'html':
        return FileText;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return Image;
      default:
        return FileText;
    }
  };

  const resetUpload = () => {
    setUploadedFile(null);
    setStep('upload');
    setUploadProgress(0);
    setMessage('');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-primary-500 to-secondary-500 text-white px-4 py-2 rounded-full text-sm font-medium mb-4">
          <Sparkles className="w-4 h-4" />
          <span>AI-Powered Translation</span>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Upload & Translate</h2>
        <p className="text-gray-600">Transform your documents with intelligent translation</p>
      </motion.div>

      {/* Step Indicator */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="flex items-center justify-center space-x-4 mb-8"
      >
        {[
          { step: 'upload', label: 'Upload', icon: Upload },
          { step: 'configure', label: 'Configure', icon: Globe },
          { step: 'translate', label: 'Translate', icon: Loader },
          { step: 'complete', label: 'Complete', icon: CheckCircle }
        ].map(({ step: stepName, label, icon: Icon }, index) => {
          const isActive = step === stepName;
          const isCompleted = ['upload', 'configure', 'translate', 'complete'].indexOf(step) > index;
          const isCurrent = step === stepName;

          return (
            <React.Fragment key={stepName}>
              <div className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isCompleted || isCurrent
                    ? 'bg-primary-500 text-white shadow-lg'
                    : 'bg-gray-200 text-gray-400'
                }`}>
                  <Icon className={`w-4 h-4 ${isCurrent && (uploading || translating) ? 'animate-spin' : ''}`} />
                </div>
                <span className={`ml-2 text-sm font-medium transition-colors ${
                  isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {label}
                </span>
              </div>
              {index < 3 && (
                <div className={`w-8 h-0.5 transition-colors ${
                  isCompleted ? 'bg-primary-500' : 'bg-gray-200'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </motion.div>

      {/* File Upload Section */}
      <AnimatePresence mode="wait">
        {step === 'upload' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
          >
            <div
              {...getRootProps()}
              className={`upload-zone relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50 scale-105'
                  : 'border-gray-300 hover:border-primary-400 hover:bg-primary-25'
              }`}
            >
              <input {...getInputProps()} />

              <motion.div
                animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
                className="space-y-6"
              >
                <div className="w-20 h-20 bg-gradient-to-br from-primary-400 to-primary-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
                  <Upload className="w-10 h-10 text-white" />
                </div>

                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {isDragActive ? 'Drop your file here!' : 'Upload your document'}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    <span className="font-semibold text-primary-600">Click to browse</span> or drag and drop your file
                  </p>
                  <div className="flex flex-wrap items-center justify-center gap-2 text-sm text-gray-500">
                    <span className="bg-gray-100 px-3 py-1 rounded-full">PDF</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">DOCX</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">TXT</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">RTF</span>
                    <span className="bg-gray-100 px-3 py-1 rounded-full">HTML</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Maximum file size: 10MB</p>
                </div>
              </motion.div>

              {uploading && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="absolute inset-0 bg-white/90 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center"
                >
                  <div className="w-16 h-16 bg-primary-500 rounded-full flex items-center justify-center mb-4 shadow-lg">
                    <Loader className="w-8 h-8 text-white animate-spin" />
                  </div>
                  <p className="text-lg font-semibold text-gray-900 mb-2">Uploading...</p>
                  <div className="w-64 bg-gray-200 rounded-full h-2 mb-2">
                    <motion.div
                      className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <p className="text-sm text-gray-600">{Math.round(uploadProgress)}% complete</p>
                </motion.div>
              )}
            </div>
          </motion.div>
        )}

        {/* Translation Configuration */}
        {(step === 'configure' || step === 'translate' || step === 'complete') && uploadedFile && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
          >
            {/* File Preview */}
            <div className="flex items-center space-x-4 mb-8 p-4 bg-gray-50/80 rounded-2xl">
              <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                {React.createElement(getFileIcon(uploadedFile.filename), {
                  className: 'w-6 h-6 text-primary-600'
                })}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">{uploadedFile.filename}</h4>
                <p className="text-sm text-gray-600">
                  {uploadedFile.file_type?.toUpperCase()} • Ready for translation
                </p>
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={resetUpload}
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </motion.button>
            </div>

            {step === 'configure' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <h3 className="text-xl font-bold text-gray-900 mb-6">Translation Settings</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Source Language
                    </label>
                    <div className="relative">
                      <select
                        value={sourceLang}
                        onChange={(e) => setSourceLang(e.target.value)}
                        className="block w-full px-4 py-3 bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all appearance-none font-medium"
                      >
                        {Object.entries(languages).map(([code, name]) => (
                          <option key={code} value={code}>{name}</option>
                        ))}
                      </select>
                      <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Target Language
                    </label>
                    <div className="relative">
                      <select
                        value={targetLang}
                        onChange={(e) => setTargetLang(e.target.value)}
                        className="block w-full px-4 py-3 bg-gray-50 border-0 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all appearance-none font-medium"
                      >
                        {Object.entries(languages).map(([code, name]) => (
                          <option key={code} value={code}>{name}</option>
                        ))}
                      </select>
                      <Globe className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-center">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleTranslate}
                    disabled={translating || sourceLang === targetLang}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 py-4 rounded-2xl text-lg font-semibold shadow-lg flex items-center space-x-3"
                  >
                    <span>Start Translation</span>
                    <ArrowRight className="w-5 h-5" />
                  </motion.button>
                </div>
              </motion.div>
            )}

            {step === 'translate' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                  <Loader className="w-10 h-10 text-white animate-spin" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Processing Translation</h3>
                <p className="text-gray-600 mb-4">AI is analyzing and translating your document...</p>
                <div className="w-64 bg-gray-200 rounded-full h-2 mx-auto">
                  <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full w-1/2 animate-pulse" />
                </div>
              </motion.div>
            )}

            {step === 'complete' && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-12"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring' }}
                  className="w-20 h-20 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg"
                >
                  <CheckCircle className="w-10 h-10 text-white" />
                </motion.div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Translation Started!</h3>
                <p className="text-gray-600 mb-6">Your document has been queued for translation. Monitor progress in the Jobs tab.</p>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={resetUpload}
                  className="bg-gradient-to-r from-primary-500 to-primary-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-shadow"
                >
                  Upload Another Document
                </motion.button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Messages */}
      <AnimatePresence>
        {message && message.includes('error') && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-center space-x-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-red-700">{message}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default FileUpload;
