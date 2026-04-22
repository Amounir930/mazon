import React, { useEffect, useRef, useState } from 'react';
import { useLogs } from '@/api/hooks';
import { X, Terminal, Trash2, ChevronLeft, ChevronRight, Pause, Play, Download } from 'lucide-react';

interface LogSidePanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const LogSidePanel: React.FC<LogSidePanelProps> = ({ isOpen, onClose }) => {
  const [isPaused, setIsPaused] = useState(false);
  const [lines, setLines] = useState(100);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { data, isLoading } = useLogs(lines, isOpen && !isPaused);
  const [status, setStatus] = useState<any>(null);

  // Fetch status once when panel opens
  useEffect(() => {
    if (isOpen) {
      import('@/api/endpoints').then(({ debugApi }) => {
        debugApi.getStatus().then(res => setStatus(res.data));
      });
    }
  }, [isOpen]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (!isPaused && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data, isPaused]);

  if (!isOpen) return null;

  const getLogLevelColor = (line: string) => {
    if (line.includes('| ERROR    |')) return 'text-red-400 font-bold';
    if (line.includes('| WARNING  |')) return 'text-yellow-400';
    if (line.includes('| DEBUG    |')) return 'text-blue-400';
    if (line.includes('| SUCCESS  |')) return 'text-green-400';
    return 'text-gray-300';
  };

  const formatLogLine = (line: string) => {
    // Regex to match the standard loguru format: 2026-04-22 17:25:00 | INFO     | ...
    const parts = line.split(' | ');
    if (parts.length >= 3) {
      const time = parts[0];
      const level = parts[1];
      const rest = parts.slice(2).join(' | ');
      return (
        <div className="py-0.5 border-b border-white/5 hover:bg-white/5 transition-colors">
          <span className="text-[10px] text-gray-500 font-mono">{time}</span>
          <span className={`mx-2 text-[10px] font-mono px-1 rounded bg-black/30 ${getLogLevelColor(line)}`}>
            {level.trim()}
          </span>
          <span className={`text-xs font-mono break-all ${getLogLevelColor(line)}`}>{rest}</span>
        </div>
      );
    }
    return <div className="text-xs font-mono text-gray-400 py-0.5">{line}</div>;
  };

  return (
    <div className={`fixed inset-y-0 right-0 w-[450px] bg-[#0d0d1a]/95 backdrop-blur-xl border-l border-white/10 shadow-2xl z-[100] flex flex-col transition-transform duration-300 transform ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-500/20 rounded-lg">
            <Terminal className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">System Logs</h3>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider">Backend Diagnostics</p>
          </div>
        </div>
        <button 
          onClick={onClose}
          className="p-2 hover:bg-white/10 rounded-full transition-colors"
        >
          <X className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-3 border-b border-white/5 bg-black/20">
        <button 
          onClick={() => setIsPaused(!isPaused)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${isPaused ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}
        >
          {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          {isPaused ? 'Resume' : 'Live'}
        </button>

        <div className="h-4 w-px bg-white/10 mx-1" />

        <select 
          value={lines}
          onChange={(e) => setLines(Number(e.target.value))}
          className="bg-white/5 border border-white/10 rounded-lg text-[10px] text-gray-300 px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value={50}>Last 50 lines</option>
          <option value={100}>Last 100 lines</option>
          <option value={500}>Last 500 lines</option>
        </select>

        <div className="flex-1" />

        <button 
          title="Download Logs"
          className="p-1.5 hover:bg-white/10 rounded text-gray-400 transition-colors"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>

      {/* Log Body */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-black/40"
      >
        {isLoading && !data ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 opacity-50">
            <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            <p className="text-xs text-gray-500 font-mono">Initializing connection...</p>
          </div>
        ) : data?.logs && data.logs.length > 0 ? (
          <div className="space-y-0.5">
            {data.logs.map((line, i) => (
              <React.Fragment key={i}>
                {formatLogLine(line)}
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full opacity-30">
            <Terminal className="w-12 h-12 mb-2" />
            <p className="text-xs font-mono">No logs available</p>
          </div>
        )}
      </div>

      {/* Footer Status */}
      <div className="p-3 border-t border-white/10 bg-white/5 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-1.5 h-1.5 rounded-full ${isPaused ? 'bg-yellow-500' : 'bg-green-500 animate-pulse'}`} />
            <span className="text-[10px] text-gray-400 font-mono uppercase">
              {isPaused ? 'Paused' : 'Monitoring Active'}
            </span>
          </div>
          <span className="text-[10px] text-gray-500 font-mono">
            {data?.total_lines || 0} total entries
          </span>
        </div>
        
        {status && (
          <div className="pt-2 border-t border-white/5 text-[9px] font-mono text-gray-500 truncate" title={status.db_url}>
            <span className="text-blue-400/50 mr-1">DB:</span> {status.db_url}
          </div>
        )}
      </div>

    </div>
  );
};

export default LogSidePanel;
