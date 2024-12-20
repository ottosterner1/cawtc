// src/components/ui/card.tsx
import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  return (
    <div className={`rounded-lg border bg-white shadow ${className}`}>
      {children}
    </div>
  );
};

export function CardHeader({ children, className = "" }: { children: React.ReactNode, className?: string }) {
  return <div className={`p-6 pb-4 ${className}`}>{children}</div>
}

export function CardTitle({ children }: { children: React.ReactNode }) {
  return <h3 className="text-lg font-medium">{children}</h3>
}

export function CardContent({ children }: { children: React.ReactNode }) {
  return <div className="p-6 pt-0">{children}</div>
}