// src/components/Card.tsx
import React from 'react';
import clsx from 'clsx';
import styles from './Card.module.css';

export interface CardProps extends React.PropsWithChildren {
  /** The main heading shown on the card */
  title: string;
  /** Optional supporting copy underneath the title */
  description?: string;
  /** Make the whole card an anchor when this is provided */
  href?: string;
  /** Optional icon or emoji rendered above the title */
  icon?: React.ReactNode;
  /** Extra class names for layout tweaks */
  className?: string;
}

/**
 * A polished card component whose visual style mirrors Mintlify's documentation cards.
 *
 * Place `Card.module.css` next to this file (contents below).
 */
export default function Card({
  title,
  description,
  href,
  icon,
  className,
  children,
}: CardProps) {
  const Inner = (
    <div className={clsx(styles.card, className)}>
      {icon && <div className={styles.icon}>{icon}</div>}
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {children && <span className={styles.inlineContent}>{children}</span>}
    </div>
  );

  return href ? (
    <a href={href} className={styles.linkWrapper}>
      {Inner}
    </a>
  ) : (
    Inner
  );
}