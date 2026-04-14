/**
 * NeonButton - High-performance neon-styled button
 * Pure CSS implementation, zero JS animation overhead
 */

import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | false | null)[]) {
  return twMerge(clsx(inputs));
}

export interface NeonButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'amazon' | 'rainbow';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  styleType?: 'solid' | 'outline' | 'ghost';
  iconOnly?: boolean;
  fullWidth?: boolean;
  isLoading?: boolean;
}

const NeonButton = forwardRef<HTMLButtonElement, NeonButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      styleType = 'solid',
      iconOnly = false,
      fullWidth = false,
      isLoading = false,
      disabled,
      className,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          'neon-btn',
          `neon-btn--${variant}`,
          `neon-btn--${size}`,
          styleType !== 'solid' && `neon-btn--${styleType}`,
          iconOnly && 'neon-btn--icon',
          fullWidth && 'neon-btn--full',
          isLoading && 'neon-btn--loading',
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {children}
      </button>
    );
  }
);

NeonButton.displayName = 'NeonButton';

export { NeonButton };
