import { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import LogSidePanel from '../debug/LogSidePanel'
import { Terminal } from 'lucide-react'

export default function Layout() {
  const [showLogs, setShowLogs] = useState(false)

  // Keyboard shortcut Ctrl+L to toggle logs
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'l') {
        e.preventDefault()
        setShowLogs(prev => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <div className="flex min-h-screen bg-bg-primary text-text-primary relative overflow-hidden" dir="rtl">
      <Sidebar />
      <main className="flex-1 overflow-auto pr-64">
        <div className="p-6">
          <Outlet />
        </div>
      </main>

      {/* Floating Log Toggle Button */}
      <button
        onClick={() => setShowLogs(true)}
        className="hidden fixed bottom-6 left-6 p-3 bg-[#1a1a2e] border border-white/10 rounded-full shadow-2xl hover:bg-blue-600/20 transition-all z-40 group"
        title="View Backend Logs (Ctrl+L)"
      >
        <Terminal className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform" />
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
      </button>

      {/* Log Side Panel */}
      <LogSidePanel isOpen={showLogs} onClose={() => setShowLogs(false)} />
    </div>
  )
}

