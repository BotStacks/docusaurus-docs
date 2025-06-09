import React from "react";
import styles from "./Note.module.css";

type NoteProps = {
  children: React.ReactNode;
  type?: "info" | "warning" | "success" | "danger";
  title?: string;
};

export default function Note({ children, type = "info", title }: NoteProps) {
  return (
    <div className={`${styles.note} ${styles[type]}`}>
      <div className={styles.header}>
        {type === "info" && "ℹ️"}
        {type === "warning" && "⚠️"}
        {type === "success" && "✅"}
        {type === "danger" && "❌"}
        <span className={styles.title}>{title || type.charAt(0).toUpperCase() + type.slice(1)}</span>
      </div>
      <div className={styles.body}>{children}</div>
    </div>
  );
}
