import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  FileText,
  Activity,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Languages,
  Sparkles,
  BarChart3,
  Book
} from 'lucide-react';

const menuItems = [
  {
    id: 'upload',
    icon: Upload,
    label: 'Upload & Translate',
    gradient: 'from-blue-500 to-purple-500'
  },
  {
    id: 'documents',
    icon: FileText,
    label: 'My Documents',
    gradient: 'from-green-500 to-teal-500'
  },
  {
    id: 'jobs',
    icon: Activity,
    label: 'Translation Jobs',
    gradient: 'from-orange-500 to-red-500'
  },
  {
    id: 'support',
    icon: Book,
    label: 'Documentation',
    gradient: 'from-indigo-500 to-blue-500'
  },
  {
    id: 'analytics',
    icon: BarChart3,
    label: 'Analytics',
    gradient: 'from-purple-500 to-pink-500'
  },
  {
    id: 'settings',
    icon: Settings,
    label: 'Settings',
    gradient: 'from-gray-500 to-gray-600'
  }
];

function Sidebar({ activeTab, setActiveTab, user, onLogout, collapsed, setCollapsed }) {
  return (
    <motion.div
      initial={{ x: -300 }}
      animate={{ x: 0, width: collapsed ? 80 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="fixed left-0 top-0 h-full bg-gradient-to-b from-secondary-900 to-secondary-800 border-r border-white/10 backdrop-blur-xl z-40 shadow-2xl"
    >
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between">
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="flex items-center space-x-3"
              >
                <div className="bg-gradient-to-r from-primary-500 to-purple-500 p-2 rounded-xl">
                  <Languages className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-white font-bold text-lg">TranslateAI</h1>
                  <p className="text-white/60 text-xs">Multi-Modal Translation</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Navigation */}
      <div className="p-4 flex-1">
        <nav className="space-y-2">
          {menuItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <motion.button
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center p-3 rounded-xl transition-all duration-300 group relative overflow-hidden ${
                  isActive
                    ? `bg-gradient-to-r ${item.gradient} shadow-lg`
                    : 'hover:bg-white/10'
                }`}
              >
                {/* Active indicator */}
                {isActive && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute left-0 top-0 bottom-0 w-1 bg-white rounded-r-full"
                  />
                )}

                {/* Icon */}
                <div className={`flex items-center justify-center ${collapsed ? 'mx-auto' : 'mr-3'}`}>
                  <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-white/70 group-hover:text-white'} transition-colors`} />
                </div>

                {/* Label */}
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      transition={{ duration: 0.2 }}
                      className={`font-medium text-sm ${
                        isActive ? 'text-white' : 'text-white/70 group-hover:text-white'
                      } transition-colors`}
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Hover effect */}
                {!isActive && (
                  <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/5 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  />
                )}
              </motion.button>
            );
          })}
        </nav>
      </div>

      {/* User info and logout */}
      <div className="p-4 border-t border-white/10">
        {/* User info */}
        <div className="mb-4">
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="bg-white/5 rounded-xl p-3 mb-3"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-semibold">
                      {user?.email?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium truncate">
                      {user?.email}
                    </p>
                    <p className="text-white/60 text-xs">Premium User</p>
                  </div>
                  <Sparkles className="w-4 h-4 text-yellow-400" />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Logout button */}
        <button
          onClick={onLogout}
          className={`w-full flex items-center p-3 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 hover:text-red-300 transition-colors group ${collapsed ? 'justify-center' : ''}`}
        >
          <LogOut className={`w-5 h-5 ${collapsed ? '' : 'mr-3'}`} />
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="font-medium text-sm"
              >
                Logout
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
    </motion.div>
  );
}

export default Sidebar;