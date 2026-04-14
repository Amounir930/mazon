/**
 * NeonCard - High-performance glassmorphism card
 */

import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | false | null)[]) {
  return twMerge(clsx(inputs));
}

export interface NeonCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'featured';
  accent?: 'blue' | 'green' | 'orange' | 'pink' | 'yellow' | 'red';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  interactive?: boolean;
  glowCorner?: boolean;
}

const NeonCard = forwardRef<HTMLDivElement, NeonCardProps>(
  (
    {
      children,
      variant = 'default',
      accent,
      size = 'md',
      interactive = false,
      glowCorner = false,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'neon-card',
          variant !== 'default' && `neon-card--${variant}`,
          accent && `neon-card--${accent}`,
          `neon-card--${size}`,
          interactive && 'neon-card--interactive',
          glowCorner && 'neon-card--glow-corner',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

NeonCard.displayName = 'NeonCard';

// Sub-components for structured cards
function NeonCardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('neon-card__header', className)} {...props} />;
}

function NeonCardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('neon-card__title', className)} {...props} />;
}

function NeonCardSubtitle({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('neon-card__subtitle', className)} {...props} />;
}

function NeonCardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('neon-card__body', className)} {...props} />;
}

function NeonCardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('neon-card__footer', className)} {...props} />;
}

// Stat card component
export interface NeonStatProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  value: string | number;
  label: string;
  change?: {
    value: number;
    direction: 'up' | 'down';
  };
}

function NeonStat({ icon, value, label, change, className, ...props }: NeonStatProps) {
  return (
    <div className={cn('neon-stat', className)} {...props}>
      {icon && <div className="neon-stat__icon">{icon}</div>}
      <span className="neon-stat__value">{value}</span>
      <span className="neon-stat__label">{label}</span>
      {change && (
        <span className={cn('neon-stat__change', `neon-stat__change--${change.direction}`)}>
          {change.direction === 'up' ? '↑' : '↓'} {Math.abs(change.value)}%
        </span>
      )}
    </div>
  );
}

NeonCard.Header = NeonCardHeader;
NeonCard.Title = NeonCardTitle;
NeonCard.Subtitle = NeonCardSubtitle;
NeonCard.Body = NeonCardBody;
NeonCard.Footer = NeonCardFooter;
NeonCard.Stat = NeonStat;

export { NeonCard };
