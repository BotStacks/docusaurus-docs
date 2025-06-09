import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/__docusaurus/debug',
    component: ComponentCreator('/__docusaurus/debug', '5ff'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/config',
    component: ComponentCreator('/__docusaurus/debug/config', '5ba'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/content',
    component: ComponentCreator('/__docusaurus/debug/content', 'a2b'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/globalData',
    component: ComponentCreator('/__docusaurus/debug/globalData', 'c3c'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/metadata',
    component: ComponentCreator('/__docusaurus/debug/metadata', '156'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/registry',
    component: ComponentCreator('/__docusaurus/debug/registry', '88c'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/routes',
    component: ComponentCreator('/__docusaurus/debug/routes', '000'),
    exact: true
  },
  {
    path: '/',
    component: ComponentCreator('/', 'df4'),
    routes: [
      {
        path: '/',
        component: ComponentCreator('/', '3cb'),
        routes: [
          {
            path: '/',
            component: ComponentCreator('/', '1f4'),
            routes: [
              {
                path: '/category/common-tasks',
                component: ComponentCreator('/category/common-tasks', 'c38'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/category/getting-started',
                component: ComponentCreator('/category/getting-started', '685'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/category/quickstart-guide',
                component: ComponentCreator('/category/quickstart-guide', '348'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/category/resources',
                component: ComponentCreator('/category/resources', '6a5'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/category/sequence-studio',
                component: ComponentCreator('/category/sequence-studio', 'd97'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/category/tools--features',
                component: ComponentCreator('/category/tools--features', '012'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/conversation-design/build-flows',
                component: ComponentCreator('/common-tasks/conversation-design/build-flows', '6a0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/conversation-design/conditions-logic',
                component: ComponentCreator('/common-tasks/conversation-design/conditions-logic', 'dce'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/conversation-design/understand-nodes',
                component: ComponentCreator('/common-tasks/conversation-design/understand-nodes', 'bfb'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/deployment/embed-chatbot',
                component: ComponentCreator('/common-tasks/deployment/embed-chatbot', 'a6d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/integrations/crm-integrations',
                component: ComponentCreator('/common-tasks/integrations/crm-integrations', 'f96'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/integrations/discord-integration',
                component: ComponentCreator('/common-tasks/integrations/discord-integration', 'd08'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/integrations/slack-integration',
                component: ComponentCreator('/common-tasks/integrations/slack-integration', '94d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/integrations/whatsapp-integration',
                component: ComponentCreator('/common-tasks/integrations/whatsapp-integration', '574'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/knowledge-management/add-knowledge-sources',
                component: ComponentCreator('/common-tasks/knowledge-management/add-knowledge-sources', 'f2a'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/knowledge-management/preview-responses',
                component: ComponentCreator('/common-tasks/knowledge-management/preview-responses', 'd4f'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/knowledge-management/prioritize-organize',
                component: ComponentCreator('/common-tasks/knowledge-management/prioritize-organize', '658'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/log-analytics/logs-analytics',
                component: ComponentCreator('/common-tasks/log-analytics/logs-analytics', '241'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/testing-and-improvement/analyze-and-improve-performance',
                component: ComponentCreator('/common-tasks/testing-and-improvement/analyze-and-improve-performance', '89e'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/testing-and-improvement/simulate-conversations-and-debug',
                component: ComponentCreator('/common-tasks/testing-and-improvement/simulate-conversations-and-debug', '81d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/testing-and-improvement/test-in-dirtbox',
                component: ComponentCreator('/common-tasks/testing-and-improvement/test-in-dirtbox', 'a69'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/common-tasks/usage-and-costs/track-costs',
                component: ComponentCreator('/common-tasks/usage-and-costs/track-costs', 'a3b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/conceptual-overview',
                component: ComponentCreator('/getting-started/conceptual-overview', 'd37'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/quickstart-guide/conversation-flow',
                component: ComponentCreator('/getting-started/quickstart-guide/conversation-flow', '4ca'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/quickstart-guide/create-botstack',
                component: ComponentCreator('/getting-started/quickstart-guide/create-botstack', '56a'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/quickstart-guide/deployment',
                component: ComponentCreator('/getting-started/quickstart-guide/deployment', 'b09'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/quickstart-guide/knowledge-base',
                component: ComponentCreator('/getting-started/quickstart-guide/knowledge-base', 'fcc'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/quickstart-guide/testing',
                component: ComponentCreator('/getting-started/quickstart-guide/testing', '149'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/getting-started/what-is-botstacks',
                component: ComponentCreator('/getting-started/what-is-botstacks', 'c95'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/resources/changelog',
                component: ComponentCreator('/resources/changelog', '313'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/resources/contact-support',
                component: ComponentCreator('/resources/contact-support', '917'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/resources/discord',
                component: ComponentCreator('/resources/discord', '609'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/resources/tutorials',
                component: ComponentCreator('/resources/tutorials', '9ff'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/activation-kit-reference',
                component: ComponentCreator('/tools-features/activation-kit-reference', 'a84'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/brain-vault',
                component: ComponentCreator('/tools-features/brain-vault', '055'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/dirtbox-reference',
                component: ComponentCreator('/tools-features/dirtbox-reference', 'af9'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/best-practices',
                component: ComponentCreator('/tools-features/sequence-studio/best-practices', '80b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/design-features',
                component: ComponentCreator('/tools-features/sequence-studio/design-features', 'bfa'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/faq',
                component: ComponentCreator('/tools-features/sequence-studio/faq', '1aa'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/node-reference',
                component: ComponentCreator('/tools-features/sequence-studio/node-reference', '7e7'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/overview',
                component: ComponentCreator('/tools-features/sequence-studio/overview', 'a93'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/tools-features/sequence-studio/panels',
                component: ComponentCreator('/tools-features/sequence-studio/panels', 'a8f'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/',
                component: ComponentCreator('/', '14c'),
                exact: true,
                sidebar: "tutorialSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
