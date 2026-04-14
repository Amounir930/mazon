/**
 * Neon UI Components Showcase
 * Demo page to test all new components
 * Pure CSS - Zero JS animation overhead
 */

import { Package, Upload, CheckCircle, XCircle, Play, Download, Mail, ShoppingCart, Settings, Check, X, User } from 'lucide-react';
import { NeonButton } from '@/components/common/NeonButton';
import { NeonCard } from '@/components/common/NeonCard';

export default function NeonShowcasePage() {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Neon UI Showcase</h1>
        <p className="text-text-secondary mt-1">مكونات جديدة بأداء عالي - Pure CSS</p>
      </div>

      {/* Buttons Section */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">الأزرار - Neon Buttons</h2>
        
        {/* Primary Variants */}
        <div className="space-y-2">
          <p className="text-sm text-text-muted">Variants</p>
          <div className="flex flex-wrap gap-4">
            <NeonButton variant="primary"><Play className="w-4 h-4" /> WATCH NOW</NeonButton>
            <NeonButton variant="info"><User className="w-4 h-4" /> LOG IN</NeonButton>
            <NeonButton variant="success"><Download className="w-4 h-4" /> DOWNLOAD</NeonButton>
            <NeonButton variant="warning"><Mail className="w-4 h-4" /> SEND NOW</NeonButton>
            <NeonButton variant="amazon"><ShoppingCart className="w-4 h-4" /> BUY NOW</NeonButton>
            <NeonButton variant="primary"><Settings className="w-4 h-4" /> SETTINGS</NeonButton>
            <NeonButton variant="success"><Check className="w-4 h-4" /> THANK YOU</NeonButton>
            <NeonButton variant="danger"><X className="w-4 h-4" /> DENIED</NeonButton>
          </div>
        </div>

        {/* Sizes */}
        <div className="space-y-2">
          <p className="text-sm text-text-muted">Sizes</p>
          <div className="flex flex-wrap gap-4 items-center">
            <NeonButton variant="primary" size="sm">Small</NeonButton>
            <NeonButton variant="primary" size="md">Medium</NeonButton>
            <NeonButton variant="primary" size="lg">Large</NeonButton>
            <NeonButton variant="primary" size="xl">Extra Large</NeonButton>
          </div>
        </div>

        {/* Styles */}
        <div className="space-y-2">
          <p className="text-sm text-text-muted">Styles</p>
          <div className="flex flex-wrap gap-4">
            <NeonButton variant="primary" styleType="solid">Solid</NeonButton>
            <NeonButton variant="primary" styleType="outline">Outline</NeonButton>
            <NeonButton variant="primary" styleType="ghost">Ghost</NeonButton>
            <NeonButton variant="rainbow">Rainbow</NeonButton>
          </div>
        </div>

        {/* States */}
        <div className="space-y-2">
          <p className="text-sm text-text-muted">States</p>
          <div className="flex flex-wrap gap-4">
            <NeonButton variant="primary" isLoading>Loading</NeonButton>
            <NeonButton variant="primary" disabled>Disabled</NeonButton>
          </div>
        </div>
      </section>

      {/* Cards Section */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">الكروت - Neon Cards</h2>
        
        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <NeonCard accent="blue">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">المنتجات</p>
                <p className="text-3xl font-bold text-text-primary mt-1">124</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
                <Package className="w-6 h-6 text-text-primary" />
              </div>
            </div>
          </NeonCard>
          
          <NeonCard accent="orange">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">في الطابور</p>
                <p className="text-3xl font-bold text-text-primary mt-1">12</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
                <Upload className="w-6 h-6 text-text-primary" />
              </div>
            </div>
          </NeonCard>
          
          <NeonCard accent="green">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">منشورة</p>
                <p className="text-3xl font-bold text-text-primary mt-1">98</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-text-primary" />
              </div>
            </div>
          </NeonCard>
          
          <NeonCard accent="red">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-secondary">فاشلة</p>
                <p className="text-3xl font-bold text-text-primary mt-1">3</p>
              </div>
              <div className="w-12 h-12 rounded-xl bg-bg-elevated/50 border border-border-subtle flex items-center justify-center">
                <XCircle className="w-6 h-6 text-text-primary" />
              </div>
            </div>
          </NeonCard>
        </div>

        {/* Interactive Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="neon-card neon-card--interactive group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amazon-orange/20 to-amazon-light/10 border border-amazon-orange/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
              <Package className="w-6 h-6 text-amazon-orange" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">إضافة منتج جديد</h3>
            <p className="text-text-secondary text-sm">أدخل بيانات المنتج وارفعه على أمازون</p>
          </div>

          <div className="neon-card neon-card--interactive group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-blue/20 to-neon-purple/10 border border-neon-blue/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
              <Upload className="w-6 h-6 text-neon-blue" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">رفع جماعي</h3>
            <p className="text-text-secondary text-sm">ارفع ملف CSV أو Excel لمنتجات متعددة</p>
          </div>

          <div className="neon-card neon-card--interactive group">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-blue/10 border border-neon-cyan/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-200">
              <CheckCircle className="w-6 h-6 text-neon-cyan" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">طابور الرفع</h3>
            <p className="text-text-secondary text-sm">تابع حالة رفع المنتجات لأمازون</p>
          </div>
        </div>
      </section>

      {/* Status Badges */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">الحالات - Status Badges</h2>
        <div className="flex flex-wrap gap-3">
          <span className="neon-badge neon-badge--blue">processing</span>
          <span className="neon-badge neon-badge--green">success</span>
          <span className="neon-badge neon-badge--yellow">queued</span>
          <span className="neon-badge neon-badge--red">failed</span>
          <span className="neon-badge neon-badge--purple">submitted</span>
        </div>
      </section>

      {/* Inputs Section */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">المدخلات - Neon Inputs</h2>
        <div className="max-w-md space-y-4">
          <div className="neon-input-group">
            <label className="neon-label">اسم المنتج</label>
            <input type="text" className="neon-input" placeholder="أدخل اسم المنتج..." />
          </div>
          
          <div className="neon-input-group">
            <label className="neon-label">السعر</label>
            <input type="number" className="neon-input neon-input--green" placeholder="0.00" />
          </div>
          
          <div className="neon-input-group">
            <label className="neon-label neon-label--required">الكمية</label>
            <input type="number" className="neon-input neon-input--orange" placeholder="0" />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" className="neon-checkbox" />
              <span className="text-text-secondary text-sm">تفعيل</span>
            </label>
            
            <label className="flex items-center gap-2">
              <input type="checkbox" className="neon-checkbox" defaultChecked />
              <span className="text-text-secondary text-sm">مفعل</span>
            </label>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input type="radio" name="radio-demo" className="neon-radio" />
              <span className="text-text-secondary text-sm">خيار 1</span>
            </label>
            
            <label className="flex items-center gap-2">
              <input type="radio" name="radio-demo" className="neon-radio" defaultChecked />
              <span className="text-text-secondary text-sm">خيار 2</span>
            </label>

            <label className="flex items-center gap-2">
              <input type="checkbox" className="neon-toggle" />
              <span className="text-text-secondary text-sm">Toggle</span>
            </label>
          </div>
        </div>
      </section>

      {/* Performance Notes */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-text-primary">ملاحظات الأداء</h2>
        <div className="neon-card neon-card--accent neon-card--green">
          <ul className="space-y-2 text-text-secondary text-sm">
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              Pure CSS animations - GPU accelerated
            </li>
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              CSS containment for complex components
            </li>
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              No Framer Motion or heavy animation libraries
            </li>
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              will-change used sparingly on hover only
            </li>
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              Zero JavaScript for hover effects
            </li>
            <li className="flex items-center gap-2">
              <span className="text-neon-cyan">✓</span>
              CSS variables for consistent theming
            </li>
          </ul>
        </div>
      </section>
    </div>
  );
}
