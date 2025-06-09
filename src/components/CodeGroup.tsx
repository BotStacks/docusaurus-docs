import React, { useState, Children, isValidElement } from "react";
import styles from "./CodeGroup.module.css";

type Tab = {
  label: string;
  language: string;
  children: React.ReactNode;
};

function parseTabs(children: React.ReactNode): Tab[] {
  // Each child is a <pre> block, typically with a className indicating the language and a "metastring" label.
  return Children.toArray(children)
    .filter(isValidElement)
    .map((child: any) => {
      // Try to get the tab label from the code fence metastring (```bash npm)
      let label = "";
      let language = "";
      if (child.props?.className) {
        // className example: "language-bash"
        const match = /language-([^\s]+)/.exec(child.props.className);
        if (match) language = match[1];
      }
      if (child.props?.metastring) {
        // Mintlify/remark-mdx might pass a label as metastring (not always set)
        label = child.props.metastring.trim();
      }
      // Fallback: if label not set, use language
      return {
        label: label || language || "Code",
        language: language || "text",
        children: child,
      };
    });
}

export default function CodeGroup({ children }: { children: React.ReactNode }) {
  const tabs = parseTabs(children);
  const [selected, setSelected] = useState(0);

  if (tabs.length === 0) return null;
  if (tabs.length === 1) return <div>{tabs[0].children}</div>;

  return (
    <div className={styles.codeGroup}>
      <div className={styles.tabBar}>
        {tabs.map((tab, i) => (
          <button
            key={i}
            className={`${styles.tab} ${i === selected ? styles.active : ""}`}
            onClick={() => setSelected(i)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className={styles.tabContent}>
        {tabs[selected].children}
      </div>
    </div>
  );
}
