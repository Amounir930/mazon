import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Package, 
  ShoppingBag, 
  RefreshCw, 
  BarChart3,
  Calendar,
  AlertTriangle
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { toast } from 'react-hot-toast';
import { useTranslation } from 'react-i18next';
import api from '@/lib/axios';

const LiveMirrorPage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  const [days, setDays] = useState(7);
  const [hasOrderPermission, setHasOrderPermission] = useState(true);

  const fetchMetrics = async (showToast = false) => {
    try {
      setLoading(true);
      const response = await api.get(`/dashboard/metrics?days=${days}`);
      if (response.data.success) {
        setMetrics(response.data.data);
        setHasOrderPermission(true);
        if (showToast) toast.success('تم تحديث البيانات الحية من أمازون');
      }
    } catch (error: any) {
      console.error('Error fetching live mirror metrics:', error);
      if (error.response?.data?.detail?.includes('403') || error.response?.status === 403) {
        setHasOrderPermission(false);
      }
      toast.error('فشل جلب بعض البيانات من أمازون');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [days]);

  const handleManualSync = async () => {
    setIsSyncing(true);
    await fetchMetrics(true);
    setIsSyncing(false);
  };

  const statCards = [
    { 
      label: 'إجمالي الوحدات المباعة', 
      value: metrics?.total_units || 0, 
      sub: `آخر ${days} يوم`,
      icon: ShoppingBag, 
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10'
    },
    { 
      label: 'مبيعات الشهر', 
      value: `${metrics?.month?.sales || 0} ${metrics?.today?.currency || 'EGP'}`, 
      sub: 'إجمالي مبيعات الفترة',
      icon: Calendar, 
      color: 'text-amber-400',
      bg: 'bg-amber-500/10'
    },
    { 
      label: 'مبيعات الأسبوع', 
      value: `${metrics?.week?.sales || 0} ${metrics?.today?.currency || 'EGP'}`, 
      sub: 'آخر 7 أيام فعلي',
      icon: BarChart3, 
      color: 'text-emerald-400', 
      bg: 'bg-emerald-500/10'
    },
    { 
      label: 'مبيعات اليوم', 
      value: `${metrics?.today?.sales || 0} ${metrics?.today?.currency || 'EGP'}`, 
      sub: 'اليوم حتى الآن',
      icon: Activity, 
      color: 'text-rose-400',
      bg: 'bg-rose-500/10'
    }
  ];

  return (
    <div className="p-6 space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            متابعة المبيعات <span className="text-cyan-500">Sales Tracking</span>
            <div className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          </h1>
          <p className="text-white/40 mt-1 font-medium">مراقبة مباشرة لمبيعات أمازون (Stateless Live Sync)</p>
        </div>
        
        <div className="flex items-center gap-3">
        <div className="flex items-center bg-white/5 border border-white/10 p-1 rounded-xl">
          {[
            { val: 7, label: '7 أيام' },
            { val: 30, label: '30 يوم' },
            { val: 90, label: '90 يوم' }
          ].map((opt) => (
            <button
              key={opt.val}
              onClick={() => setDays(opt.val)}
              className={`px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
                days === opt.val 
                  ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20' 
                  : 'text-white/40 hover:text-white/70 hover:bg-white/5'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

          <button 
            onClick={handleManualSync}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all duration-300 shadow-lg ${
              isSyncing 
                ? 'bg-white/10 text-white/30 cursor-not-allowed' 
                : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-900/20'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
            مزامنة حية
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, i) => (
          <div key={i} className="group relative bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 overflow-hidden transition-all hover:bg-white/10">
            <div className={`absolute -right-4 -top-4 w-24 h-24 ${card.bg} rounded-full blur-3xl group-hover:scale-125 transition-all`} />
            <div className="relative flex items-center justify-between">
              <div className="space-y-1">
                <p className="text-xs font-bold text-white/40 uppercase tracking-widest">{card.label}</p>
                <p className="text-2xl font-black text-white">{card.value}</p>
                <p className="text-[10px] text-white/30 font-medium">{card.sub}</p>
              </div>
              <div className={`w-12 h-12 rounded-2xl ${card.bg} flex items-center justify-center border border-white/5 shadow-inner`}>
                <card.icon className={`w-6 h-6 ${card.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sales Chart */}
        <div className="lg:col-span-2 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-8 h-[500px] flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              أداء المبيعات
            </h3>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-cyan-500" />
                <span className="text-xs text-white/60">إجمالي المبيعات</span>
              </div>
            </div>
          </div>
          
          <div className="flex-1 w-full">
            {loading ? (
              <div className="w-full h-full bg-white/5 rounded-2xl animate-pulse" />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics?.chart_data || []}>
                  <defs>
                    <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="date" stroke="rgba(255,255,255,0.3)" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.3)" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    itemStyle={{ fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="sales" stroke="#06b6d4" strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Recently Sold Products */}
        <div className="lg:col-span-1 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 flex flex-col h-[500px]">
          <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-amber-400" />
            {t('dashboard.recentlySold')}
          </h3>
          <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar pr-2">
            {loading ? (
              Array(5).fill(0).map((_, i) => (
                <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />
              ))
            ) : metrics?.leaderboard && metrics.leaderboard.length > 0 ? (
              metrics.leaderboard.map((item: any, idx: number) => (
                <div key={idx} className="group bg-white/5 hover:bg-white/10 p-4 rounded-xl border border-white/5 transition-all">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center text-xs font-black text-cyan-400">
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-white truncate" title={item.name}>{item.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-white/30 font-mono">SKU: {item.sku}</span>
                        <span className="text-[10px] text-white/30">•</span>
                        <span className="text-[10px] text-amber-400/60 font-medium">{item.date}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-black text-emerald-400">+{item.quantity}</p>
                      <p className="text-[9px] text-white/40">{item.price} {metrics?.today?.currency}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : !hasOrderPermission ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-12 h-12 rounded-full bg-amber-500/10 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-amber-500" />
                </div>
                <div>
                  <p className="text-sm font-bold text-white mb-1">صلاحية "الطلبات" غير مفعلة</p>
                  <p className="text-[10px] text-white/40 leading-relaxed">
                    Orders API Access Denied (403).<br/>
                    يرجى تفعيل دور <strong>Direct-to-Consumer Shipping</strong> في Amazon Developer Console وتحديث IAM Policy.
                  </p>
                </div>
                <button 
                  onClick={() => window.open('https://developer.amazonservices.com', '_blank')}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[10px] text-white/60 transition-colors"
                >
                  فتح مركز المطورين Amazon Console
                </button>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-white/20 italic text-center px-4">
                <p>{t('dashboard.noRecentSales')}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMirrorPage;
