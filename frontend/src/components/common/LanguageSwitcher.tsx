/**
 * Language Switcher Component
 * Toggles between Arabic and English
 * Updates document direction (RTL/LTR)
 */

import { useTranslation } from 'react-i18next'
import { Globe } from 'lucide-react'

export function LanguageSwitcher() {
  const { i18n } = useTranslation()
  const currentLang = i18n.language

  const toggleLanguage = () => {
    const newLang = currentLang === 'ar' ? 'en' : 'ar'
    i18n.changeLanguage(newLang)
    // Update document direction
    document.documentElement.dir = newLang === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.lang = newLang
  }

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 px-3 py-2 rounded-xl bg-bg-elevated/50 border border-border-subtle hover:border-border-medium hover:bg-bg-hover transition-all text-text-secondary hover:text-text-primary"
      title={currentLang === 'ar' ? 'Switch to English' : 'التبديل للعربية'}
    >
      <Globe className="w-4 h-4" />
      <span className="text-sm font-medium">
        {currentLang === 'ar' ? 'EN' : 'ع'}
      </span>
    </button>
  )
}
