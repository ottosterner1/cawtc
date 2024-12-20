import * as React from "react"

interface AlertProps {
  children: React.ReactNode;
  className?: string;
}

export function Alert({ children, className = "" }: AlertProps) {
  return (
    <div className={`p-4 rounded-lg border ${className}`}>
      {children}
    </div>
  )
}

export function AlertTitle({ children }: { children: React.ReactNode }) {
  return <h5 className="font-medium mb-1">{children}</h5>
} 