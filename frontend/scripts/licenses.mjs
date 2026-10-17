import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'

const packages = ['react', 'react-dom', 'scheduler', 'chart.js', '@kurkle/color', 'lucide-react', 'zod', '@fontsource/ibm-plex-sans', '@fontsource/ibm-plex-mono']
const destination = path.resolve('dist/third-party-licenses')
await mkdir(destination, { recursive: true })
const manifest = []
for (const name of packages) {
  const directory = path.resolve('node_modules', name)
  const metadata = JSON.parse(await readFile(path.join(directory, 'package.json'), 'utf8'))
  let legal = null
  for (const candidate of ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'license', 'OFL.txt']) {
    try { legal = await readFile(path.join(directory, candidate), 'utf8'); break } catch { /* Check the package's next conventional license filename. */ }
  }
  if (!legal) throw new Error(`Missing production dependency license: ${name}`)
  const file = name.replaceAll('/', '_').replaceAll('@', '') + '.txt'
  await writeFile(path.join(destination, file), legal)
  manifest.push({ name, version: metadata.version, license: metadata.license, file })
}
await writeFile(path.join(destination, 'index.json'), JSON.stringify(manifest, null, 2) + '\n')
console.log(`Retained ${manifest.length} production dependency notices`)
for (const file of ['LICENSE', 'NOTICE.md']) {
  await writeFile(path.resolve('dist', file), await readFile(path.resolve('..', file)))
}