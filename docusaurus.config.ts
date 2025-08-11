const {themes: prismThemes} = require('prism-react-renderer');

/** @type {import('@docusaurus/types').Config} */
module.exports = {
  title: 'BotStacks Developer',
  url: 'https://docs.botstacks.ai',
  baseUrl: '/',
  favicon: 'favicon.svg',
  organizationName: 'BotStacks',
  projectName: 'botstacks-developer',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',
  i18n: { defaultLocale: 'en', locales: ['en'] },
  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: { 
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js') },
        theme: { customCss: require.resolve('./src/css/custom.css') },
      },
    ],
  ],
  plugins: [
    // short name works if the package is resolvable from root
    'docusaurus-plugin-image-zoom',
    require.resolve('docusaurus-lunr-search'),
    [
      '@docusaurus/plugin-client-redirects',
      {
        redirects: [
          // Redirect broken URLs to correct ones
          {
            from: '/getting-started/what-is-botstacks/quickstart-guide/create-botstack',
            to: '/getting-started/quickstart-guide/create-botstack',
          },
          {
            from: '/resource-center/overview',
            to: '/resources/changelog',
          },
          {
            from: '/tools-features/02-common-tasks/02-conversation-design/01-build-flows',
            to: '/common-tasks/conversation-design/build-flows',
          },
          {
            from: '/tools-features/02-common-tasks/02-conversation-design/03-conditions-logic',
            to: '/common-tasks/conversation-design/conditions-logic',
          },
          {
            from: '/tools-features/02-common-tasks/04-testing-and-improvement/01-test-in-dirtbox',
            to: '/common-tasks/testing-and-improvement/test-in-dirtbox',
          },
          {
            from: '/tools-features/common-tasks/conversation-design/build-flows',
            to: '/common-tasks/conversation-design/build-flows',
          },
          {
            from: '/tools-features/common-tasks/conversation-design/understand-nodes',
            to: '/common-tasks/conversation-design/understand-nodes',
          },
          {
            from: '/tools-features/sequence-studio/faq/05-best-practices.mdx',
            to: '/tools-features/sequence-studio/best-practices',
          },
          {
            from: '/tools-features/sequence-studio/faq/05-best-practices',
            to: '/tools-features/sequence-studio/best-practices',
          },
          {
            from: '/tools-features/sequence-studio/overview/node-reference',
            to: '/tools-features/sequence-studio/node-reference',
          },
        ],

      },
    ],
  ],

  themeConfig: /** @type {import('@docusaurus/preset-classic').ThemeConfig} */ ({
    image: 'static/img/docusaurus-social-card.jpg',
    navbar: {
      //title: 'BotStacks Developer',
      logo: { alt: 'BotStacks Logo', src: 'images/logo/light.svg', srcDark: 'images/logo/dark.svg', className: 'navbar-logo' },
      items: [
        //{ to: '/', label: 'Home', position: 'left' },
        //{ type: 'docSidebar', sidebarId: 'tutorialSidebar', position: 'left', label: 'Docs' },
        { to: 'mailto:support@botstacks.ai', label: 'Contact Us', position: 'right', className: 'hide-on-mobile' },
        { to: 'https://dashboard.botstacks.ai', label: 'Dashboard', position: 'right', className: 'button button--primary dashboard-link hide-on-mobile' },
      ],
    },
    footer: {
      links: [
        {
          items: [
            { label: 'Twitter', to: 'https://twitter.com/botstacks' },
            { label: 'GitHub', to: 'https://github.com/BotStacks' },
            { label: 'LinkedIn', to: 'https://www.linkedin.com/company/botstacks' },
            { label: 'YouTube', to: 'https://www.youtube.com/@BotStacksai/videos' },
            { label: 'Discord', to: 'https://discord.gg/suMCX9NZSs' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} BotStacks. Built with Docusaurus.`,
    },
    prism: { theme: prismThemes.github, darkTheme: prismThemes.dracula },
    colorMode: { defaultMode: 'dark', disableSwitch: true },
    zoom: {
      selector: '.markdown > img',      // which images to target
      background: {
      light: 'transparent',
      dark: '#0d0f14',
      },
      config: {
        margin: 90,
      },
    },
  }),
};