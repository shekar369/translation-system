import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Book,
  Globe,
  FileText,
  Download,
  Upload,
  CheckCircle,
  Clock,
  AlertCircle,
  Languages,
  FileType,
  Workflow,
  Info,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';
import toast from 'react-hot-toast';

function Support({ token }) {
  const [supportedLanguages, setSupportedLanguages] = useState({});
  const [copiedAPI, setCopiedAPI] = useState('');

  useEffect(() => {
    fetchSupportedLanguages();
  }, []);

  const fetchSupportedLanguages = async () => {
    try {
      const response = await fetch('/api/translate/languages', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setSupportedLanguages(data.languages);
      }
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedAPI(type);
    setTimeout(() => setCopiedAPI(''), 2000);
    toast.success('Copied to clipboard!');
  };

  const supportedFormats = [
    { ext: 'PDF', desc: 'Portable Document Format', icon: '📄', status: 'Full Support' },
    { ext: 'DOCX', desc: 'Microsoft Word Document', icon: '📝', status: 'Full Support' },
    { ext: 'TXT', desc: 'Plain Text File', icon: '📄', status: 'Full Support' },
    { ext: 'RTF', desc: 'Rich Text Format', icon: '📄', status: 'Full Support' },
    { ext: 'HTML', desc: 'HyperText Markup Language', icon: '🌐', status: 'Full Support' }
  ];

  const workflowSteps = [
    { step: 1, title: 'Upload Document', desc: 'Upload your document using drag-and-drop or file picker', icon: Upload, status: 'active' },
    { step: 2, title: 'Select Languages', desc: 'Choose source and target languages from 12+ supported options', icon: Languages, status: 'active' },
    { step: 3, title: 'Start Translation', desc: 'AI extracts text and translates using Google Translator API', icon: Workflow, status: 'active' },
    { step: 4, title: 'Download Result', desc: 'Download translated text file when processing completes', icon: Download, status: 'active' }
  ];

  const apiEndpoints = [
    { method: 'GET', endpoint: '/api/files/', desc: 'List all uploaded documents' },
    { method: 'POST', endpoint: '/api/files/upload', desc: 'Upload a new document' },
    { method: 'POST', endpoint: '/api/translate/', desc: 'Create translation job' },
    { method: 'GET', endpoint: '/api/translate/jobs', desc: 'List translation jobs' },
    { method: 'GET', endpoint: '/api/translate/jobs/{id}/download', desc: 'Download translated file' },
    { method: 'GET', endpoint: '/api/translate/languages', desc: 'Get supported languages' }
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <div className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white px-4 py-2 rounded-full text-sm font-medium mb-4">
          <Book className="w-4 h-4" />
          <span>Documentation & Support</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Translation System Guide</h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Comprehensive guide to using our AI-powered document translation system
        </p>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          { label: 'Supported Languages', value: Object.keys(supportedLanguages).length, icon: Globe, color: 'from-blue-500 to-blue-600' },
          { label: 'File Formats', value: supportedFormats.length, icon: FileType, color: 'from-green-500 to-green-600' },
          { label: 'API Endpoints', value: apiEndpoints.length, icon: ExternalLink, color: 'from-purple-500 to-purple-600' },
          { label: 'Processing Time', value: '~3s', icon: Clock, color: 'from-orange-500 to-orange-600' }
        ].map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.1 + index * 0.05 }}
              className="bg-white/80 backdrop-blur-xl rounded-2xl p-6 shadow-lg border border-gray-200/50 text-center"
            >
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${stat.color} mb-3`}>
                <Icon className="w-6 h-6 text-white" />
              </div>
              <div className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</div>
              <div className="text-sm text-gray-600">{stat.label}</div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Supported Languages */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Supported Languages</h2>
            <p className="text-gray-600">Translate between any of these {Object.keys(supportedLanguages).length} languages</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Object.entries(supportedLanguages).map(([code, name]) => (
            <motion.div
              key={code}
              whileHover={{ scale: 1.02 }}
              className="flex items-center space-x-3 p-4 bg-gray-50/80 rounded-xl hover:bg-gray-100/80 transition-colors"
            >
              <div className="w-10 h-10 bg-gradient-to-r from-blue-400 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">{code.toUpperCase()}</span>
              </div>
              <div>
                <div className="font-semibold text-gray-900">{name}</div>
                <div className="text-xs text-gray-500">{code}</div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Supported File Formats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 bg-gradient-to-r from-green-500 to-green-600 rounded-xl">
            <FileType className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Supported File Formats</h2>
            <p className="text-gray-600">Upload documents in any of these formats (max 10MB)</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {supportedFormats.map((format) => (
            <motion.div
              key={format.ext}
              whileHover={{ scale: 1.02 }}
              className="flex items-center space-x-4 p-6 bg-gray-50/80 rounded-2xl hover:bg-gray-100/80 transition-colors"
            >
              <div className="text-3xl">{format.icon}</div>
              <div className="flex-1">
                <div className="font-bold text-gray-900">{format.ext}</div>
                <div className="text-sm text-gray-600">{format.desc}</div>
                <div className="inline-flex items-center space-x-1 mt-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="text-xs text-green-600 font-medium">{format.status}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Translation Workflow */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
      >
        <div className="flex items-center space-x-3 mb-8">
          <div className="p-3 bg-gradient-to-r from-purple-500 to-purple-600 rounded-xl">
            <Workflow className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">How Translation Works</h2>
            <p className="text-gray-600">Step-by-step process from upload to download</p>
          </div>
        </div>

        <div className="space-y-8">
          {workflowSteps.map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                className="flex items-start space-x-6"
              >
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl flex items-center justify-center">
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-xl font-bold text-gray-900">Step {item.step}: {item.title}</h3>
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                  <p className="text-gray-600 leading-relaxed">{item.desc}</p>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className="absolute left-8 top-16 w-0.5 h-8 bg-gradient-to-b from-purple-300 to-purple-200"></div>
                )}
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* API Documentation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl">
            <ExternalLink className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">API Reference</h2>
            <p className="text-gray-600">RESTful API endpoints for developers</p>
          </div>
        </div>

        <div className="space-y-4">
          {apiEndpoints.map((api, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 + index * 0.05 }}
              className="flex items-center justify-between p-4 bg-gray-50/80 rounded-xl hover:bg-gray-100/80 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <div className={`px-3 py-1 rounded-lg text-xs font-bold text-white ${
                  api.method === 'GET' ? 'bg-blue-500' : 'bg-green-500'
                }`}>
                  {api.method}
                </div>
                <div className="font-mono text-sm text-gray-800">{api.endpoint}</div>
                <div className="text-gray-600">{api.desc}</div>
              </div>
              <button
                onClick={() => copyToClipboard(`${api.method} ${api.endpoint}`, api.endpoint)}
                className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              >
                {copiedAPI === api.endpoint ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Copy className="w-4 h-4 text-gray-500" />
                )}
              </button>
            </motion.div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-blue-50/80 rounded-xl border border-blue-200/50">
          <div className="flex items-center space-x-2 mb-2">
            <Info className="w-5 h-5 text-blue-500" />
            <span className="font-semibold text-blue-900">Authentication Required</span>
          </div>
          <p className="text-blue-700 text-sm">
            All API requests require Bearer token authentication. Include the header:
            <code className="ml-1 px-2 py-1 bg-blue-100 rounded">Authorization: Bearer YOUR_TOKEN</code>
          </p>
        </div>
      </motion.div>

      {/* Technical Details */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-gray-200/50 p-8"
      >
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-3 bg-gradient-to-r from-gray-500 to-gray-600 rounded-xl">
            <Info className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Technical Specifications</h2>
            <p className="text-gray-600">System capabilities and limitations</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h3 className="font-bold text-gray-900 text-lg">Capabilities</h3>
            <ul className="space-y-2">
              {[
                'Text extraction from PDF, DOCX, TXT, RTF, HTML',
                'AI-powered translation using Google Translator API',
                'Batch processing with job queue system',
                'Real-time progress tracking',
                'Downloadable translated files',
                'RESTful API with authentication'
              ].map((item, index) => (
                <li key={index} className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-4">
            <h3 className="font-bold text-gray-900 text-lg">Limitations</h3>
            <ul className="space-y-2">
              {[
                'Maximum file size: 10MB',
                'Text-only translation (no images/charts)',
                'Processing time varies by document length',
                'Requires internet connection for translation API',
                'Translated files are in TXT format only',
                'No real-time collaborative translation'
              ].map((item, index) => (
                <li key={index} className="flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 text-orange-500 flex-shrink-0" />
                  <span className="text-gray-700">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </motion.div>

      {/* Contact Support */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-8 text-white text-center"
      >
        <h2 className="text-3xl font-bold mb-4">Need Help?</h2>
        <p className="text-blue-100 mb-6 text-lg">
          Our support team is here to help you with any questions or issues
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-white text-blue-600 px-6 py-3 rounded-xl font-semibold hover:bg-blue-50 transition-colors">
            Contact Support
          </button>
          <button className="bg-blue-500/50 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-500/70 transition-colors">
            View Documentation
          </button>
        </div>
      </motion.div>
    </div>
  );
}

export default Support;