import { execFileSync } from 'node:child_process'
import { basename, dirname } from 'node:path'
import type { Options as DocsOptions } from '@docusaurus/plugin-content-docs'
import type { Options as ThemeOptions } from '@docusaurus/theme-classic'
import type { UserThemeConfig } from '@docusaurus/theme-common'
import type { Config } from '@docusaurus/types'
import { copyConfiguratorFiles } from './scripts/configurator-files.mts'
import { repoFacts } from './scripts/repo-facts.mts'
import tableLayout from './scripts/table-layout.mts'
// title, description, address and repository: also read by tools/social_card.py
import site from './site.json'

// GitHub Pages: DOCS_URL is the site origin, DOCS_BASE_URL the path of the edition (pages.yml builds main under /Feeder/next/)
const baseUrl = process.env.DOCS_BASE_URL ?? site.baseUrl
const repo = `https://github.com/${site.repo}`

const config = async (): Promise<Config> => ({
  title: site.title,
  tagline: site.description,
  url: process.env.DOCS_URL ?? site.url,
  baseUrl,
  favicon: 'assets/favicon.svg',
  trailingSlash: true,
  titleDelimiter: '-',
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {
    // .mdx pages are MDX; the .md partials that build.py --guide writes to docs/_generated/ are plain Markdown
    format: 'detect',
    hooks: { onBrokenMarkdownLinks: 'throw' },
    // every page's description (link preview, search engines) is the site's; Docusaurus would take the first
    // paragraph. Partials (_*.mdx, docs/_generated/) take no front matter.
    parseFrontMatter: async (params) => {
      const result = await params.defaultParseFrontMatter(params)
      const partial = [params.filePath, dirname(params.filePath)].some((p) => basename(p).startsWith('_'))
      if (!partial) result.frontMatter.description ??= site.description
      return result
    },
  },
  // the search box of src/theme/SearchBar.tsx: it reads the index next to this script
  stylesheets: [`${baseUrl}pagefind/pagefind-component-ui.css`],
  scripts: [{ src: `${baseUrl}pagefind/pagefind-component-ui.js`, defer: true }],
  // the pieces of the classic preset the site uses, without its blog, pages, SVG-as-component and search plugins
  themes: [
    [
      '@docusaurus/theme-classic',
      // brand.css: tokens and their mapping, shared by the OpenReloading sites; feeder.css: this site's layout
      { customCss: ['./src/css/brand.css', './src/css/feeder.css'] } satisfies ThemeOptions,
    ],
  ],
  plugins: [
    // the pages in the left column (sidebars.ts), no breadcrumbs above them
    [
      '@docusaurus/plugin-content-docs',
      {
        routeBasePath: '/',
        sidebarPath: './sidebars.ts',
        breadcrumbs: false,
        rehypePlugins: [tableLayout],
      } satisfies DocsOptions,
    ],
    '@docusaurus/plugin-sitemap',
    // build/guide/buildguide.json is written by build.py --guide
    ['@openreloading/docusaurus-plugin-buildguide', { data: '../build/guide/buildguide.json' }],
    ({ siteDir }) => ({
      name: 'configurator-files',
      postBuild: ({ outDir }) => {
        const copied = copyConfiguratorFiles(`${siteDir}/../build/configurator`, outDir)
        console.info(
          copied
            ? `[configurator] copied ${copied} print files`
            : '[configurator] no print files in build/configurator/: the configurator page shows its notice',
        )
      },
    }),
    // the search index of the built site (scripts/search.mts), in its own process: the config loader cannot
    // require the ESM-only pagefind package
    ({ siteDir }) => ({
      name: 'search-index',
      postBuild: ({ outDir }) => {
        execFileSync(process.execPath, ['scripts/search.mts', outDir], { cwd: siteDir, stdio: 'inherit' })
      },
    }),
  ],
  themeConfig: {
    // link previews: og:image and twitter:image from `image`, the rest on every page (404 included); X reads
    // og:title and og:description where twitter:title and twitter:description are missing
    image: 'assets/social-card.png',
    metadata: [
      { name: 'description', content: site.description },
      { property: 'og:description', content: site.description },
      { property: 'og:type', content: 'website' },
      { property: 'og:site_name', content: site.title },
      { property: 'og:image:type', content: 'image/png' },
      { property: 'og:image:width', content: '1200' },
      { property: 'og:image:height', content: '630' },
      { property: 'og:image:alt', content: 'OpenReloading Feeder logo above the site description' },
    ],
    navbar: {
      // the wordmark of each scheme names the site, no title beside it
      logo: { alt: site.title, src: 'assets/logo.svg', srcDark: 'assets/logo-dark.svg' },
      items: [
        // read once per build, the browser makes no request to GitHub
        { type: 'custom-repo', repo: site.repo, facts: await repoFacts(site.repo), position: 'right' },
        { type: 'search', position: 'right' },
      ],
    },
    footer: {
      links: [
        { label: 'Source on GitHub', href: repo },
        { label: 'Build guide', to: '/' },
        { label: 'MIT licence', href: `${repo}/blob/main/LICENSE` },
      ],
    },
    colorMode: { respectPrefersColorScheme: true },
    // code in the token colours: the commands on the pages have no language to highlight
    prism: { theme: { plain: { color: 'var(--ink)', backgroundColor: 'var(--surface-alt)' }, styles: [] } },
  } satisfies UserThemeConfig,
})

export default config
