import React from "react";
import styles from "./Check.module.css";

type CheckProps = {
  children: React.ReactNode;
};

export default function Check({ children }: CheckProps) {
  return (
    <div className={styles.check}>
      <span className={styles.icon} aria-label="Check" role="img">✔️</span>
      <span className={styles.text}>{children}</span>
    </div>
  );
}
