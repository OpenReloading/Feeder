// Copies the configurator's print files and manifest.json (build.py --configurator, build/configurator/) into the built
// site next to the configurator page (postBuild in docusaurus.config.ts). Without them the page says that the files are
// built on release.
import { copyFileSync, existsSync, mkdirSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

/** The number of files copied from `src` to `<outDir>/configurator/data/`, 0 when `src` has no manifest.json. */
export function copyConfiguratorFiles(src: string, outDir: string): number {
  if (!existsSync(join(src, 'manifest.json'))) return 0
  const dest = join(outDir, 'configurator', 'data')
  mkdirSync(dest, { recursive: true })
  const files = [...readdirSync(src).filter((f) => f.endsWith('.stl')), 'manifest.json']
  for (const f of files) copyFileSync(join(src, f), join(dest, f))
  return files.length
}
