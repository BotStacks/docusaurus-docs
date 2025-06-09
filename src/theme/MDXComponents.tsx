import React from 'react';
// Importing the original mapper + our components according to the Docusaurus doc
import MDXComponents from '@theme-original/MDXComponents';
import Card from '@site/src/components/Card';
export default {
  // Reusing the default mapping
  ...MDXComponents,
  Card,
};