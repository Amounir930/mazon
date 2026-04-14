/**
 * Performance Optimizations for Crazy Lister
 * Zero-dependency, pure React features
 */

import { lazy, Suspense, Component, ReactNode } from 'react';

// ============================================
// Lazy Loading with Error Boundary
// ============================================

export function lazyLoad<T extends React.ComponentType<any>>(
  factory: () => Promise<{ default: T }>,
  fallback?: ReactNode
) {
  const Component = lazy(factory);
  
  return function LazyComponent(props: React.ComponentProps<T>) {
    return (
      <Suspense fallback={fallback || <LoadingSpinner />}>
        <Component {...props} />
      </Suspense>
    );
  };
}

// ============================================
// Lightweight Loading Spinner (Pure CSS)
// ============================================

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-full min-h-[200px]">
      <div className="relative w-12 h-12">
        <div className="absolute inset-0 rounded-full border-2 border-border-subtle"></div>
        <div className="absolute inset-0 rounded-full border-2 border-amazon-orange border-t-transparent animate-spin"></div>
      </div>
    </div>
  );
}

// ============================================
// Error Boundary
// ============================================

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center h-full min-h-[200px] gap-4">
            <div className="w-16 h-16 rounded-full bg-neon-red/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-neon-red" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-text-primary">حدث خطأ غير متوقع</h3>
            <p className="text-sm text-text-secondary">حاول إعادة تحميل الصفحة</p>
            <button
              onClick={() => window.location.reload()}
              className="neon-btn neon-btn--danger"
            >
              إعادة تحميل
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

// ============================================
// Debounce Hook (No dependencies)
// ============================================

import { useState, useEffect, useRef } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// ============================================
// Throttle Hook (No dependencies)
// ============================================

export function useThrottle<T>(value: T, interval: number): T {
  const [throttledValue, setThrottledValue] = useState<T>(value);
  const lastRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    const now = Date.now();
    const remaining = interval - (now - lastRef.current);

    if (remaining <= 0) {
      setThrottledValue(value);
      lastRef.current = now;
    } else {
      timeoutRef.current = setTimeout(() => {
        setThrottledValue(value);
        lastRef.current = Date.now();
      }, remaining);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [value, interval]);

  return throttledValue;
}

// ============================================
// Intersection Observer Hook (Lazy loading images)
// ============================================

export function useIntersectionObserver(
  options?: IntersectionObserverInit
): [React.RefCallback<HTMLElement>, boolean] {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLElement | null>(null);

  const callback: React.RefCallback<HTMLElement> = (node) => {
    if (node) {
      elementRef.current = node;
      const observer = new IntersectionObserver(([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      }, options);
      observer.observe(node);
    }
  };

  return [callback, isVisible];
}
