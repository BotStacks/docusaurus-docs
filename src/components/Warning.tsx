import React from "react";
import styles from "./Warning.module.css";

type WarningProps = {
  children: React.ReactNode;
};

export default function Warning({ children }: WarningProps) {
  return (
    <div className={styles.warning}>
      <span className={styles.icon} aria-label="Warning" role="img">⚠️</span>
      <span className={styles.text}>{children}</span>
    </div>
  );
}
