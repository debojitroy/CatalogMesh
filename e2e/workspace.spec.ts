import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('map all supplier-marketplace routes, inspect Laya, review and export', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Map all connections' }).click()
  await expect(page.getByRole('button', { name: 'Map all connections' })).toBeEnabled()
  await expect(page.locator('.destination').first()).toContainText('Recorded', { ignoreCase: true })
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: 'test-results/connections-desktop.png', fullPage: true })
  await page.locator('.destination').first().click()
  const dialog = page.getByRole('dialog', { name: 'Inside the Laya decision' })
  await expect(dialog).toContainText('Protective earbud case covers')
  await expect(dialog).toContainText('Candidate distribution')
  await page.getByLabel('Review note').fill('Confirmed from the product description.')
  await page.getByRole('button', { name: 'Save review' }).click()
  await expect(dialog).not.toBeVisible()
  await page.getByRole('button', { name: 'Mapping ledger' }).click()
  await expect(page.getByText('Reviewed', { exact: true })).toBeVisible()
  const download = page.waitForEvent('download')
  await page.getByRole('link', { name: 'Export CSV' }).click()
  expect((await download).suggestedFilename()).toBe('catalogmesh-mappings.csv')
  await page.reload()
  await page.getByRole('button', { name: 'Mapping ledger' }).click()
  await expect(page.getByText('Reviewed', { exact: true })).toBeVisible()
})

test('import another marketplace and reject fabricated recorded predictions', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Connect marketplace', exact: true }).click()
  await page.getByLabel('Catalog definition').fill(
    JSON.stringify({
      id: 'test-market',
      name: 'Test destination',
      version: '1',
      region: 'Test taxonomy',
      categories: [
        { id: 'audio', path: 'Audio / Devices', description: 'Complete earbuds and headphones' },
        { id: 'parts', path: 'Audio / Parts', description: 'Protective cases and ear tips' },
      ],
    }),
  )
  await page.getByRole('button', { name: 'Connect catalog' }).click()
  await expect(page.locator('.matrix')).toContainText('Test destination')
  await page.getByRole('button', { name: 'Map all connections' }).click()
  await expect(page.getByRole('alert')).toContainText('Use live Laya')
})

test('evaluation exposes quality gates, failures and reproducible evidence', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Evaluation', exact: true }).click()
  await expect(page.getByText('72 decisions', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Failure explorer' })).toBeVisible()
  await expect(page.getByText('Pilot quality gate not met')).toBeVisible()
  await page.screenshot({ path: 'test-results/evaluation-desktop.png', fullPage: true })
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze()
  expect(
    results.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
    })),
  ).toEqual([])
})

test('mobile layout and connections accessibility', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(
    page.getByRole('heading', { name: 'Every catalog. Every destination.' }),
  ).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.screenshot({ path: 'test-results/connections-mobile.png', fullPage: true })
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze()
  expect(
    results.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
    })),
  ).toEqual([])
})
