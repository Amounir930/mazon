/**
 * ValidationDisplay Component
 * ============================
 * عرض رسائل الفحص والتحقق من القواعس
 */

import React from 'react';
import { ValidationIssue } from '@/services/ProductRulesValidator';

export interface ValidationDisplayProps {
  issues: ValidationIssue[];
  compact?: boolean;
}

export const ValidationDisplay: React.FC<ValidationDisplayProps> = ({
  issues,
  compact = false,
}) => {
  if (!issues || issues.length === 0) {
    return null;
  }

  const errors = issues.filter(i => i.severity === 'error');
  const warnings = issues.filter(i => i.severity === 'warning');
  const successes = issues.filter(i => i.severity === 'success');

  if (compact) {
    return (
      <div className="flex gap-4 text-sm mb-4">
        {errors.length > 0 && (
          <div className="text-red-600 font-semibold">
            ❌ {errors.length} أخطاء
          </div>
        )}
        {warnings.length > 0 && (
          <div className="text-yellow-600 font-semibold">
            ⚠️ {warnings.length} تحذيرات
          </div>
        )}
        {successes.length > 0 && (
          <div className="text-green-600 font-semibold">
            ✅ {successes.length} موافق
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3 mb-4 p-4 bg-gray-50 rounded-lg">
      {/* الأخطاء */}
      {errors.map((issue, idx) => (
        <div
          key={`error-${idx}`}
          className="flex items-start gap-3 p-3 bg-red-50 border-r-4 border-red-500 rounded"
        >
          <span className="text-red-600 text-xl mt-0.5">❌</span>
          <div className="flex-1">
            <div className="font-semibold text-red-700">{issue.message}</div>
            {issue.wordCount !== undefined && issue.minRequired !== undefined && (
              <div className="text-xs text-red-600 mt-1">
                الكلمات: {issue.wordCount} / {issue.minRequired}
              </div>
            )}
          </div>
        </div>
      ))}

      {/* التحذيرات */}
      {warnings.map((issue, idx) => (
        <div
          key={`warning-${idx}`}
          className="flex items-start gap-3 p-3 bg-yellow-50 border-r-4 border-yellow-500 rounded"
        >
          <span className="text-yellow-600 text-xl mt-0.5">⚠️</span>
          <div className="flex-1">
            <div className="font-semibold text-yellow-700">{issue.message}</div>
          </div>
        </div>
      ))}

      {/* النجاحات */}
      {successes.map((issue, idx) => (
        <div
          key={`success-${idx}`}
          className="flex items-start gap-3 p-3 bg-green-50 border-r-4 border-green-500 rounded"
        >
          <span className="text-green-600 text-xl mt-0.5">✅</span>
          <div className="flex-1">
            <div className="font-semibold text-green-700">{issue.message}</div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Inline version for single fields
export const ValidationInline: React.FC<{ issue?: ValidationIssue }> = ({
  issue,
}) => {
  if (!issue) return null;

  const colorMap = {
    error: 'text-red-600 border-red-300 bg-red-50',
    warning: 'text-yellow-600 border-yellow-300 bg-yellow-50',
    success: 'text-green-600 border-green-300 bg-green-50',
  };

  const iconMap = {
    error: '❌',
    warning: '⚠️',
    success: '✅',
  };

  return (
    <div
      className={`text-sm mt-2 p-2 border rounded ${colorMap[issue.severity]}`}
    >
      <div className="flex items-start gap-2">
        <span>{iconMap[issue.severity]}</span>
        <div className="flex-1">
          <div>{issue.message}</div>
          {issue.wordCount !== undefined && issue.minRequired !== undefined && (
            <div className="text-xs mt-1 opacity-75">
              {issue.wordCount} / {issue.minRequired} كلمة
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Summary card
export const ValidationSummary: React.FC<{
  errors: number;
  warnings: number;
  success: number;
  canSubmit: boolean;
}> = ({ errors, warnings, success, canSubmit }) => {
  return (
    <div
      className={`p-4 rounded-lg border-2 ${
        canSubmit
          ? 'bg-green-50 border-green-300'
          : 'bg-red-50 border-red-300'
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{errors}</div>
            <div className="text-xs text-red-600">أخطاء</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{warnings}</div>
            <div className="text-xs text-yellow-600">تحذيرات</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{success}</div>
            <div className="text-xs text-green-600">موافق</div>
          </div>
        </div>
        <div>
          {canSubmit ? (
            <div className="text-green-700 font-bold">
              ✅ جاهز للإرسال
            </div>
          ) : (
            <div className="text-red-700 font-bold">
              ❌ يجب إصلاح الأخطاء
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ValidationDisplay;
