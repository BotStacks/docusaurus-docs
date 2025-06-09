import React, { useState, Children, isValidElement } from "react";
import styles from "./Tabs.module.css";

type TabsProps = {
  children: React.ReactNode;
  defaultIndex?: number;
};

type TabProps = {
  title: string;
  children: React.ReactNode;
};

export function Tabs({ children, defaultIndex = 0 }: TabsProps) {
  const tabs = Children.toArray(children).filter(isValidElement) as React.ReactElement<TabProps>[];
  const [selected, setSelected] = useState(defaultIndex);

  if (tabs.length === 0) return null;
  if (tabs.length === 1) return <div>{tabs[0]}</div>;

  return (
    <div className={styles.tabs}>
      <div className={styles.tabBar}>
        {tabs.map((tab, i) => (
          <button
            key={i}
            className={`${styles.tab} ${i === selected ? styles.active : ""}`}
            onClick={() => setSelected(i)}
            type="button"
          >
            {tab.props.title}
          </button>
        ))}
      </div>
      <div className={styles.tabContent}>
        {tabs[selected]}
      </div>
    </div>
  );
}

export function Tab({ children }: TabProps) {
  // Just returns children; logic handled by Tabs
  return <div>{children}</div>;
}
