# Kibo, a Ghost theme

The Ghost theme of [Reaching Kibo](https://www.reachingkibo.com/), a French marketing strategy site with a long-form playbook called Basecamp.

It is a fork of [Source](https://github.com/TryGhost/Source) 1.7.6, the default Ghost theme, under the same MIT license. It keeps Portal, search, editor card styles and `{{ghost_head}}`, and adds:

- a field-notebook layout for long reading: sources announced up front and numbered, reading column, table of contents in the margin on desktop;
- Basecamp navigation: breadcrumb, chapter map, an ascent route between pages (camps before and after the current page, then the summit);
- a page cartridge (double rule, large stencil chapter number) and large stencil section numbers;
- structured data: `BreadcrumbList` on Basecamp pages and an `ItemList` on the hub, injected client-side from the visible page, next to the JSON-LD Ghost already outputs;
- keyboard and screen reader support: skip link, landmarks, visible focus on every control, 44 px touch targets.

Interface strings are in French. Some templates assume the Reaching Kibo content model (a `basecamp` hub and chapter tags); adapt them before using the theme elsewhere.

## Fonts

The theme uses **Supreme** and **Bespoke Stencil** from [Fontshare](https://www.fontshare.com/), under the Fontshare Free Font License (FFL). The fonts are not redistributed here. Before building a zip:

1. Download [Supreme](https://www.fontshare.com/fonts/supreme) and [Bespoke Stencil](https://www.fontshare.com/fonts/bespoke-stencil) from Fontshare.
2. Copy these WOFF2 files into `assets/fonts/`, with these exact names:
   - `Supreme-Regular.woff2`, `Supreme-Italic.woff2`, `Supreme-Medium.woff2`, `Supreme-Bold.woff2`
   - `BespokeStencil-Bold.woff2`, `BespokeStencil-Extrabold.woff2`

Without them, the browser falls back to the system fonts.

## Development

Node 22.12 or later, with npm or pnpm.

```bash
npm install
npx gulp build    # assets/built/, committed
npm test          # gscan, the Ghost theme validator, on a clean copy
npx gulp zip      # dist/kibo.zip, to upload in Ghost Admin > Settings > Design
```

Do not run `gscan .` in the working tree: gscan deletes `.git` and `node_modules` from the folder it checks. `npm test` copies the theme first.

## Contributing

`main` only changes through pull requests. Each pull request runs the CI: tracked-file checks (no font binaries, source maps, personal e-mail addresses, local paths or tokens), a fresh build that must match the committed `assets/built/`, and gscan. Write commit messages in English.

Maintainer changes are prepared in a private repository, then promoted as a single commit on a `promotion/<sha>` branch. The Promote workflow opens the pull request, which is reviewed and merged like any other change. The commit's `Transit-Commit` trailer records the private commit it came from.

## License

MIT, see [LICENSE](LICENSE). Source is © Ghost Foundation.
