// @ts-check
import { themes as prismThemes } from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Parag Ekbote',
  tagline: 'LLM Research | Optimization',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://paragekbote.github.io',
  baseUrl: '/',

  organizationName: 'ParagEkbote',
  projectName: 'ParagEkbote.github.io',

  onBrokenLinks: 'throw',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: false,   // ✅ disabled
        blog: false,   // ✅ disabled
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/docusaurus-social-card.jpg',

      colorMode: {
        respectPrefersColorScheme: true,
      },

      // ✅ CLEAN NAVBAR (no docs/blog dependency)
      navbar: {
        title: 'Parag Ekbote',
        logo: {
          alt: 'Logo',
          src: 'img/logo.svg',
        },
        items: [
          { to: '/', label: 'Home', position: 'left' },
          { to: '/research', label: 'Research', position: 'left' },
          { to: '/code', label: 'Code & OSS', position: 'left' },
          { to: '/projects', label: 'Projects', position: 'left' },
          {
            href: 'https://github.com/ParagEkbote',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },

      // ✅ CLEAN FOOTER (no docs/blog links)
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Contact',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/ParagEkbote',
              },
              {
                label: 'LinkedIn',
                href: 'https://linkedin.com/in/parag-ekbote',
              },
              {
                label: 'Email',
                href: 'mailto:your-email@example.com',
              },
            ],
          },
        ],
        copyright: `© ${new Date().getFullYear()} Parag Ekbote`,
      },

      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;