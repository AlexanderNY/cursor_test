import { HTMLAttributes } from 'react'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass'
}

export function Card({ className = '', variant = 'default', children, ...props }: CardProps) {
  const baseStyles = 'rounded-2xl p-6'
  
  const variantStyles = {
    default: 'bg-[var(--bg-secondary)] border border-[var(--border-color)]',
    glass: 'bg-[var(--bg-secondary)]/80 backdrop-blur-xl border border-[var(--border-color)]',
  }

  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${className}`} {...props}>
      {children}
    </div>
  )
}

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {}

export function CardHeader({ className = '', children, ...props }: CardHeaderProps) {
  return (
    <div className={`mb-6 ${className}`} {...props}>
      {children}
    </div>
  )
}

interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {}

export function CardTitle({ className = '', children, ...props }: CardTitleProps) {
  return (
    <h2 className={`text-2xl font-semibold text-[var(--text-primary)] ${className}`} {...props}>
      {children}
    </h2>
  )
}

interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {}

export function CardDescription({ className = '', children, ...props }: CardDescriptionProps) {
  return (
    <p className={`text-[var(--text-secondary)] mt-1 ${className}`} {...props}>
      {children}
    </p>
  )
}

interface CardContentProps extends HTMLAttributes<HTMLDivElement> {}

export function CardContent({ className = '', children, ...props }: CardContentProps) {
  return (
    <div className={className} {...props}>
      {children}
    </div>
  )
}

interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {}

export function CardFooter({ className = '', children, ...props }: CardFooterProps) {
  return (
    <div className={`mt-6 pt-6 border-t border-[var(--border-color)] ${className}`} {...props}>
      {children}
    </div>
  )
}


