import { z } from 'zod'

const scalar = z.union([z.string().max(2400), z.number().finite(), z.null()])
const table = z.object({
  id: z.string(),
  title: z.string(),
  columns: z.array(z.string()).max(8),
  rows: z.array(z.array(scalar).max(8)).max(30),
  status: z.enum(['available', 'unavailable']),
  note: z.string(),
})
const secureUrl = z
  .string()
  .url()
  .refine((value) => {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password
  })
export const ReportSchema = z.object({
  question: z.string().max(1200).default(''),
  id: z.string().uuid(),
  created_at: z.string(),
  mode: z.enum(['sample', 'live']),
  ticker: z.string().max(20),
  name: z.string().max(160),
  currency: z.string(),
  description: z.string(),
  sector: z.string(),
  price: z.number().finite().nonnegative().nullable(),
  previous_close: z.number().finite().nonnegative().nullable(),
  price_as_of: z.string(),
  price_kind: z.string(),
  history: z
    .array(
      z.object({
        date: z.string(),
        close: z.number().finite().nonnegative(),
        volume: z.number().nullable(),
      }),
    )
    .max(260),
  metrics: z.array(z.object({ label: z.string(), value: scalar, unit: z.string() })),
  tables: z.array(table),
  news: z.array(
    z.object({
      title: z.string(),
      publisher: z.string(),
      url: secureUrl,
      published_at: z.string(),
    }),
  ),
  summary: z.string(),
  analysis_kind: z.enum(['reference', 'evidence', 'ai']),
  sources: z.array(z.object({ name: z.string(), url: secureUrl, observed_at: z.string() })),
  limitations: z.array(z.string()),
})
export type Report = z.infer<typeof ReportSchema>
export type Table = z.infer<typeof table>
export const SamplesSchema = z.array(ReportSchema).min(1).max(10)
export const ConfigSchema = z.object({
  private_api: z.boolean(),
  live_data: z.boolean(),
  ai: z.boolean(),
  version: z.string(),
})
export const SavedSchema = z.array(
  z.object({ id: z.string().uuid(), ticker: z.string(), created_at: z.string() }),
)
export const MatchesSchema = z
  .array(z.object({ ticker: z.string(), name: z.string(), exchange: z.string() }))
  .max(6)
export type Saved = z.infer<typeof SavedSchema>

export function apiOrigin(value: string): string {
  const url = new URL(value)
  const local = ['127.0.0.1', 'localhost', '[::1]'].includes(url.hostname)
  if (
    (url.protocol !== 'https:' && !(local && url.protocol === 'http:')) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash ||
    url.pathname !== '/'
  )
    throw new Error('Use an HTTPS API origin, or HTTP on localhost.')
  return url.origin
}

export async function requestJson(
  origin: string,
  path: string,
  token: string,
  options: RequestInit = {},
): Promise<unknown> {
  const headers = new Headers(options.headers)
  if (token) headers.set('Authorization', 'Bearer ' + token)
  if (options.body) headers.set('Content-Type', 'application/json')
  const response = await fetch(origin + path, {
    ...options,
    headers,
    redirect: 'error',
    cache: 'no-store',
    credentials: 'omit',
  })
  if (!response.ok) {
    let message = `Request failed (${response.status}).`
    try {
      const error = (await response.json()) as { detail?: unknown }
      if (typeof error.detail === 'string') message = error.detail.slice(0, 300)
    } catch {
      /* Status remains sufficient when a response is not JSON. */
    }
    throw new Error(message)
  }
  const text = await response.text()
  if (text.length > 500_000) throw new Error('API response exceeds the workspace limit.')
  return JSON.parse(text) as unknown
}

export function exportReport(report: Report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `market-insight-${report.ticker.replace(/[^A-Z0-9.-]/g, '')}.json`
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
