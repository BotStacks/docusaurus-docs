import React from "react";
import styles from "./Steps.module.css";

type StepsProps = {
  children: React.ReactNode;
};

export function Steps({ children }: StepsProps) {
  return (
    <ol className={styles.steps}>
      {React.Children.map(children, (child, i) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<any>, { index: i })
          : child
      )}
    </ol>
  );
}

type StepProps = {
  title: string;
  children: React.ReactNode;
  index?: number;
};

export function Step({ title, children, index }: StepProps) {
  return (
    <li className={styles.step}>
      <div className={styles.stepHeader}>
        <span className={styles.stepNumber}>{(index ?? 0) + 1}</span>
        <span className={styles.stepTitle}>{title}</span>
      </div>
      <div className={styles.stepBody}>{children}</div>
    </li>
  );
}
