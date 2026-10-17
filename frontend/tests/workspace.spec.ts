import { test, expect } from '@playwright/test'

test('sample workspace loads and chart contains actual pixels', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  await expect(page.getByText('Fictional sample data')).toBeVisible()
  const canvas = page.getByRole('img', { name: 'Historical closing price chart' })
  await expect(canvas).toBeVisible()
  expect(
    await canvas.evaluate((element) => {
      const canvas = element as HTMLCanvasElement
      const data = canvas.getContext('2d')!.getImageData(0, 0, canvas.width, canvas.height).data
      let pixels = 0
      for (let index = 3; index < data.length; index += 4) if (data[index]) pixels++
      return pixels
    }),
  ).toBeGreaterThan(500)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  expect(errors).toEqual([])
  await page.screenshot({
    path: `test-results/workspace-${test.info().project.name}.png`,
    fullPage: true,
  })
})

test('every research section and company is usable', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  for (const [tab, heading] of [
    ['Financials', 'Income statement'],
    ['Ownership', 'Institutional holders'],
    ['Events', 'Dividend history'],
    ['Analysts', 'Analyst coverage'],
    ['News', 'News & disclosures'],
  ]) {
    await page.getByRole('button', { name: tab, exact: true }).click()
    await expect(page.getByRole('heading', { name: heading })).toBeVisible()
  }
  await page.getByRole('button', { name: /DEMO-B/ }).click()
  await expect(page.getByRole('heading', { name: 'Cedar Energy' })).toBeVisible()
  await page.getByRole('button', { name: '1M', exact: true }).click()
  await expect(page.getByRole('button', { name: '1M', exact: true })).toHaveClass('active')
})

test('sample lookup and unavailable symbol handling', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  await page.getByRole('textbox', { name: 'Ticker symbol' }).fill('Meridian')
  await page.getByRole('button', { name: 'Find company or ticker' }).click()
  await page.locator('.lookup-results button').click()
  await page.getByRole('button', { name: 'Research', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Meridian Health' })).toBeVisible()
  await page.getByRole('textbox', { name: 'Ticker symbol' }).fill('UNKNOWN')
  await page.getByRole('button', { name: 'Research', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('not in the synthetic reference set')
})

test('JSON export contains provenance and sample label', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  const downloading = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export JSON' }).click()
  const download = await downloading
  expect(download.suggestedFilename()).toBe('market-insight-DEMO-A.json')
  const stream = await download.createReadStream()
  let data = ''
  for await (const chunk of stream!) data += chunk.toString()
  const report = JSON.parse(data)
  expect(report.mode).toBe('sample')
  expect(report.sources.length).toBeGreaterThan(0)
})

test('private connection research history and disconnect use real API', async ({
  page,
  baseURL,
}) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  await page.getByRole('button', { name: 'API connection' }).click()
  await page.getByRole('textbox', { name: 'API origin' }).fill(baseURL!)
  await page.getByLabel('Access token').fill('fixture-' + 'X'.repeat(40))
  await page.getByRole('button', { name: 'Connect', exact: true }).click()
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await expect(page.getByText('Private API connected')).toBeVisible()
  await page.getByRole('button', { name: 'Research', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Research', exact: true })).toBeEnabled()
  await page.getByRole('button', { name: 'Saved research', exact: true }).click()
  await expect(page.locator('.saved-list button').first()).toBeVisible()
  await page.locator('.saved-list button').first().click()
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  await page.getByRole('button', { name: 'Saved research', exact: true }).click()
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Clear saved reports' }).click()
  await expect(page.getByText('No saved reports.')).toBeVisible()
  await page.getByRole('button', { name: 'Close saved research' }).click()
  await page.getByRole('button', { name: 'API connection' }).click()
  await page.getByRole('button', { name: 'Disconnect', exact: true }).click()
  await expect(page.getByText('Synthetic reference', { exact: true })).toBeVisible()
  expect(
    await page.evaluate(() => Object.keys(localStorage).some((key) => /token/i.test(key))),
  ).toBe(false)
})

test('invalid connection is explicit and tokens are not persisted', async ({ page, baseURL }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'API connection' }).click()
  await page.getByRole('textbox', { name: 'API origin' }).fill('http://untrusted.example')
  await page.getByLabel('Access token').fill('fixture-' + 'X'.repeat(40))
  await page.getByRole('button', { name: 'Connect', exact: true }).click()
  await expect(page.locator('.dialog-error')).toContainText('HTTPS')
  await page.getByRole('textbox', { name: 'API origin' }).fill(baseURL!)
  await page.getByLabel('Access token').fill('wrong-token-' + 'Y'.repeat(40))
  await page.getByRole('button', { name: 'Connect', exact: true }).click()
  await expect(page.locator('.dialog-error')).toContainText('Authentication')
})

test('source-provided markup is rendered as text', async ({ page }) => {
  await page.route('**/demo.json', async (route) => {
    const response = await route.fetch()
    const reports = await response.json()
    reports[0].description = '<img src=x onerror="window.injected=true">'
    await route.fulfill({ response, json: reports })
  })
  await page.goto('/')
  await expect(
    page.getByText('<img src=x onerror="window.injected=true">', { exact: true }),
  ).toBeVisible()
  expect(await page.evaluate(() => 'injected' in window)).toBe(false)
})

test('reference loading failure can be retried', async ({ page }) => {
  let attempts = 0
  await page.route('**/demo.json', async (route) => {
    attempts++
    if (attempts === 1) await route.fulfill({ status: 503, body: 'unavailable' })
    else await route.continue()
  })
  await page.goto('/')
  await expect(page.getByText('Reference data could not be loaded. Please retry.')).toBeVisible()
  await page.getByRole('button', { name: 'Retry', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
})

test('connection dialog supports keyboard dismissal and focus restoration', async ({ page }) => {
  await page.goto('/')
  const opener = page.getByRole('button', { name: 'API connection' })
  await opener.click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await expect(opener).toBeFocused()
})

test('narrow mobile has no page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Northstar Systems' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  expect(await page.evaluate(() => innerWidth)).toBe(320)
})
