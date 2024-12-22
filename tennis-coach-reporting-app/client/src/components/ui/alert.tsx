import * as React from "react"

interface AlertProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'destructive';
}

export function Alert({ children, className = "", variant = "default" }: AlertProps) {
  return (
    <div className={`p-4 rounded-lg border ${variant === 'destructive' ? 'border-red-600 bg-red-50' : ''} ${className}`}>
      {children}
    </div>
  )
}

export function AlertTitle({ children }: { children: React.ReactNode }) {
  return <h5 className="font-medium mb-1">{children}</h5>
}

export function AlertDescription({ children }: { children: React.ReactNode }) {
  return <div className="text-sm">{children}</div>
} 