import React from 'react';
import clsx from 'clsx';

interface CardGroupProps extends React.PropsWithChildren {
  /** Number of columns in the grid (1-4). Default = 2 */
  cols?: 1 | 2 | 3 | 4;
  className?: string;
}

/**
 * Simple CSS-grid wrapper that lays out <Card> children.
 * Drop this next to Card.tsx.
 */
export default function CardGroup({
  cols = 2,
  className,
  children,
}: CardGroupProps) {
  return (
    <div
      className={clsx('card-group', className)}
      style={{
        display: 'grid',
        gap: '1.5rem',
        gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
      }}
    >
      {children}
    </div>
  );
}
