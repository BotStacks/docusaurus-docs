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
  ],

  themeConfig: /** @type {import('@docusaurus/preset-classic').ThemeConfig} */ ({
    image: 'static/img/docusaurus-social-card.jpg',
    navbar: {
      //title: 'BotStacks Developer',
      logo: { alt: 'BotStacks Logo', src: 'images/logo/light.svg', srcDark: 'images/logo/dark.svg' },
      items: [
        //{ to: '/', label: 'Home', position: 'left' },
        //{ type: 'docSidebar', sidebarId: 'tutorialSidebar', position: 'left', label: 'Docs' },
        { to: 'mailto:support@botstacks.ai', label: 'Contact Us', position: 'right' },
        { to: 'https://dashboard.botstacks.ai', label: 'Dashboard', position: 'right', className: 'button button--primary dashboard-link' },
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