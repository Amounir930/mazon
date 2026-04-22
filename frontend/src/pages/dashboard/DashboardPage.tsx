import React from 'react';
import { 
  LayoutDashboard, 
  Package, 
  Upload, 
  CheckCircle, 
  XCircle, 
  Plus, 
  RefreshCw,
  Activity,
  Search
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import api from '@/lib/axios';
import { useQuery } from '@tanstack/react-query';

const DashboardPage: React.FC = () => {
  const { t } = useTranslation();

  // Fetch local system stats (not live Amazon sales)
  const { data: stats, isLoading } = useQuery({
    queryKey: ['system-stats'],
    queryFn: async () => {
      const response = await api.get('/products'); // Assuming this returns local product list
      const products = response.data.data || [];
      return {
        total: products.length,
        queued: products.filter((p: any) => p.status === 'pending').length,
        published: products.filter((p: any) => p.status === 'published' || p.status === 'active').length,
        failed: products.filter((p: any) => p.status === 'error' || p.status === 'failed').length
      };
    }
  });

  const cards = [
    { label: 'إجمالي المنتجات', value: stats?.total || 0, sub: 'المسجلة محلياً', icon: Package, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
    { label: 'في قائمة الانتظار', value: stats?.queued || 0, sub: 'بانتظار الرفع', icon: Upload, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'تم الرفع بنجاح', value: stats?.published || 0, sub: 'موجود على أمازون', icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'عمليات فشلت', value: stats?.failed || 0, sub: 'تحتاج مراجعة', icon: XCircle, color: 'text-rose-400', bg: 'bg-rose-500/10' }
  ];

  return (
    <div className="p-6 space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            لوحة التحكم <span className="text-amazon-orange">Dashboard</span>
          </h1>
          <p className="text-white/40 mt-1 font-medium">مرحباً بك في نظام إدارة منتجات أمازون الآلي</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, i) => (
          <div key={i} className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 flex items-center justify-between transition-all hover:bg-white/10">
            <div className="space-y-1">
              <p className="text-xs font-bold text-white/40 uppercase tracking-widest">{card.label}</p>
              <p className="text-2xl font-black text-white">{isLoading ? '...' : card.value}</p>
              <p className="text-[10px] text-white/30 font-medium">{card.sub}</p>
            </div>
            <div className={`w-12 h-12 rounded-2xl ${card.bg} flex items-center justify-center border border-white/5 shadow-inner`}>
              <card.icon className={`w-6 h-6 ${card.color}`} />
            </div>
          </div>
        ))}
      </div>

      {/* Main Actions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quick Actions */}
        <div className="space-y-6">
          <Link
            to="/products/create"
            className="group bg-gradient-to-br from-white/5 to-white/[0.02] hover:to-white/10 rounded-3xl border border-white/10 p-8 flex items-center gap-8 transition-all duration-500 hover:-translate-y-1 shadow-xl"
          >
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amazon-orange to-amazon-light flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-amazon-orange/20">
              <Plus className="w-10 h-10 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">إضافة منتج جديد</h3>
              <p className="text-white/40 mt-1">أدخل بيانات المنتج وقم برفعه مباشرة إلى أمازون</p>
            </div>
          </Link>

          <Link
            to="/listings"
            className="group bg-gradient-to-br from-white/5 to-white/[0.02] hover:to-white/10 rounded-3xl border border-white/10 p-8 flex items-center gap-8 transition-all duration-500 hover:-translate-y-1 shadow-xl"
          >
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-lg shadow-cyan-500/20">
              <RefreshCw className="w-10 h-10 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white">قائمة الانتظار</h3>
              <p className="text-white/40 mt-1">تابع حالة رفع ومعالجة المنتجات على أمازون</p>
            </div>
          </Link>
        </div>

        {/* Info Section */}
        <div className="bg-white/5 backdrop-blur-md rounded-3xl border border-white/10 p-8 flex flex-col justify-center relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none select-none">
             <LayoutDashboard className="w-64 h-64" />
          </div>
          <h3 className="text-2xl font-bold text-white mb-4">اكتشف أداء مبيعاتك <span className="text-amazon-orange ml-2 text-lg">Sales Performance</span></h3>
          <p className="text-white/60 mb-8 leading-relaxed">
            تم نقل بيانات المبيعات المباشرة والرسوم البيانية إلى قسم <strong>"متابعة المبيعات | Sales Tracking"</strong> الجديد لضمان أداء أسرع ومراقبة دقيقة لحظة بلحظة.
          </p>
          <Link 
            to="/live-mirror"
            className="inline-flex items-center gap-3 px-8 py-4 bg-amazon-orange hover:bg-amazon-light text-white font-bold rounded-2xl transition-all shadow-lg shadow-amazon-orange/20 active:scale-95 self-start"
          >
            <Activity className="w-5 h-5" />
            انتقل لمتابعة المبيعات (Live)
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
