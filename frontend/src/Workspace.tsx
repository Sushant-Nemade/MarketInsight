import { useEffect, useRef, useState } from 'react'
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  FileText,
  History,
  Link2,
  LoaderCircle,
  LogOut,
  Search,
  Settings2,
  ShieldCheck,
  Trash2,
  X,
} from 'lucide-react'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-mono/400.css'
import {
  ConfigSchema,
  MatchesSchema,
  ReportSchema,
  SamplesSchema,
  SavedSchema,
  apiOrigin,
  exportReport,
  requestJson,
} from './contracts'
import type { Report, Saved, Table } from './contracts'
import { PriceChart } from './PriceChart'
import './workspace.css'

const sections = ['overview', 'financials', 'ownership', 'events', 'analysts', 'news'] as const
type Section = (typeof sections)[number]
const labels: Record<Section, string> = {
  overview: 'Overview',
  financials: 'Financials',
  ownership: 'Ownership',
  events: 'Events',
  analysts: 'Analysts',
  news: 'News',
}
const groups: Record<Section, string[]> = {
  overview: [],
  financials: ['income', 'balance', 'cashflow'],
  ownership: ['institutional', 'major', 'mutual', 'insiders'],
  events: ['dividends', 'splits'],
  analysts: ['recommendations', 'analyst_summary'],
  news: [],
}
const money = (value: number | null, currency = '') =>
  value === null
    ? 'Unavailable'
    : new Intl.NumberFormat('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 }).format(
        value,
      ) + (currency ? ' ' + currency : '')
const compact = (value: string | number | null) =>
  value === null
    ? 'Unavailable'
    : typeof value === 'number'
      ? new Intl.NumberFormat('en-US', {
          notation: Math.abs(value) >= 1_000_000 ? 'compact' : 'standard',
          maximumFractionDigits: 2,
        }).format(value)
      : value
const dateLabel = (value: string) => (value ? value.slice(0, 10) : 'Not supplied')

function FinancialTable({ table }: { table: Table }) {
  return (
    <section className="data-section">
      <div className="section-title">
        <h3>{table.title}</h3>
        <span className="small muted">{table.rows.length} records</span>
      </div>
      {table.status === 'available' && table.note && <p className="small muted">{table.note}</p>}
      {table.status === 'unavailable' ? (
        <p className="empty">{table.note || 'Data unavailable'}</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                {table.columns.map((column, index) => (
                  <th key={index}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, index) => (
                <tr key={index}>
                  {row.map((value, cell) => (
                    <td key={cell}>{compact(value)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default function Workspace() {
  const [samples, setSamples] = useState<Report[]>([])
  const [report, setReport] = useState<Report | null>(null)
  const [loadError, setLoadError] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [reload, setReload] = useState(0)
  const [busy, setBusy] = useState(false)
  const [section, setSection] = useState<Section>('overview')
  const [range, setRange] = useState(126)
  const [query, setQuery] = useState('')
  const [question, setQuestion] = useState('Summarize the available evidence and its limitations.')
  const [useAi, setUseAi] = useState(false)
  const [connectionOpen, setConnectionOpen] = useState(false)
  const [originDraft, setOriginDraft] = useState(
    window.location.protocol.startsWith('http') ? window.location.origin : 'http://127.0.0.1:8790',
  )
  const [tokenDraft, setTokenDraft] = useState('')
  const [connection, setConnection] = useState<{
    origin: string
    token: string
    live: boolean
    ai: boolean
  } | null>(null)
  const [saved, setSaved] = useState<Saved>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [matches, setMatches] = useState<{ ticker: string; name: string; exchange: string }[]>([])
  const controller = useRef<AbortController | null>(null)

  function loadSamples() {
    setLoading(true)
    setLoadError('')
    setReload((value) => value + 1)
  }

  useEffect(() => {
    const abort = new AbortController()
    fetch(import.meta.env.BASE_URL + 'demo.json', { cache: 'no-store', signal: abort.signal })
      .then((response) => {
        if (!response.ok) throw new Error('Reference data unavailable')
        return response.json()
      })
      .then((value) => {
        const data = SamplesSchema.parse(value)
        if (!abort.signal.aborted) {
          setSamples(data)
          setReport(data[0])
          setQuery(data[0].ticker)
        }
      })
      .catch(() => {
        if (!abort.signal.aborted) setLoadError('Reference data could not be loaded. Please retry.')
      })
      .finally(() => {
        if (!abort.signal.aborted) setLoading(false)
      })
    return () => {
      abort.abort()
      controller.current?.abort()
    }
  }, [reload])

  useEffect(() => {
    if (!connectionOpen && !historyOpen) return
    const previous = document.activeElement as HTMLElement | null
    const dialog = document.querySelector('.modal')
    const first = dialog?.querySelector<HTMLElement>('input,button')
    first?.focus()
    function keyboard(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setConnectionOpen(false)
        setHistoryOpen(false)
        setTokenDraft('')
      }
      if (event.key === 'Tab' && dialog) {
        const items = Array.from(
          dialog.querySelectorAll<HTMLElement>(
            'button:not(:disabled),input:not(:disabled),a[href]',
          ),
        )
        if (event.shiftKey && document.activeElement === items[0]) {
          event.preventDefault()
          items[items.length - 1]?.focus()
        } else if (!event.shiftKey && document.activeElement === items[items.length - 1]) {
          event.preventDefault()
          items[0]?.focus()
        }
      }
    }
    document.addEventListener('keydown', keyboard)
    return () => {
      document.removeEventListener('keydown', keyboard)
      previous?.focus()
    }
  }, [connectionOpen, historyOpen])

  function selectSample(value: Report) {
    controller.current?.abort()
    controller.current = null
    setReport(value)
    setQuery(value.ticker)
    setSection('overview')
    setError('')
    setBusy(false)
    setMatches([])
  }

  async function connect(event: React.FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const origin = apiOrigin(originDraft)
      const config = ConfigSchema.parse(
        await requestJson(origin, '/api/config', '', { signal: AbortSignal.timeout(8000) }),
      )
      const history = SavedSchema.parse(
        await requestJson(origin, '/api/reports', tokenDraft, {
          signal: AbortSignal.timeout(8000),
        }),
      )
      if (!config.private_api) throw new Error('Private API is not configured.')
      setConnection({ origin, token: tokenDraft, live: config.live_data, ai: config.ai })
      setSaved(history)
      setTokenDraft('')
      setConnectionOpen(false)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'API connection failed.')
    }
  }

  function disconnect() {
    controller.current?.abort()
    setConnection(null)
    setTokenDraft('')
    setUseAi(false)
    setSaved([])
    setHistoryOpen(false)
    setBusy(false)
    if (samples[0]) selectSample(samples[0])
  }

  async function lookup() {
    setError('')
    setMatches([])
    if (!query.trim()) return
    if (!connection) {
      const needle = query.toLowerCase()
      setMatches(
        samples
          .filter((sample) => (sample.name + sample.ticker).toLowerCase().includes(needle))
          .map((sample) => ({ ticker: sample.ticker, name: sample.name, exchange: 'Synthetic' })),
      )
      return
    }
    try {
      setMatches(
        MatchesSchema.parse(
          await requestJson(
            connection.origin,
            '/api/search?query=' + encodeURIComponent(query.trim()),
            connection.token,
            { signal: AbortSignal.timeout(55000) },
          ),
        ),
      )
    } catch {
      setError('Symbol lookup unavailable. Check the query and live-data settings.')
    }
  }

  async function research(event?: React.FormEvent) {
    event?.preventDefault()
    setError('')
    setMatches([])
    const ticker = query.trim().toUpperCase()
    if (!/^[A-Z0-9^][A-Z0-9.^=-]{0,19}$/.test(ticker)) {
      setError('Enter a valid ticker symbol.')
      return
    }
    if (!connection) {
      const match = samples.find((sample) => sample.ticker === ticker)
      if (!match) {
        setError('This symbol is not in the synthetic reference set.')
        return
      }
      setReport(match)
      return
    }
    const sample = ticker.startsWith('DEMO-')
    if (!sample && !connection.live) {
      setError('Live data access is disabled by the API owner.')
      return
    }
    controller.current?.abort()
    const abort = new AbortController()
    controller.current = abort
    const timeout = setTimeout(() => abort.abort(), 90000)
    setBusy(true)
    try {
      const result = ReportSchema.parse(
        await requestJson(connection.origin, '/api/research', connection.token, {
          method: 'POST',
          signal: abort.signal,
          body: JSON.stringify({
            ticker,
            question,
            sections: [...sections],
            analysis: useAi && !sample ? 'ai' : 'evidence',
            data_mode: sample ? 'sample' : 'live',
          }),
        }),
      )
      if (!abort.signal.aborted) {
        setReport(result)
        setSaved(
          SavedSchema.parse(
            await requestJson(connection.origin, '/api/reports', connection.token, {
              signal: abort.signal,
            }),
          ),
        )
      }
    } catch (reason) {
      if (controller.current === abort) {
        if (!abort.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Research failed.')
        else setError('Research cancelled or timed out.')
      }
    } finally {
      clearTimeout(timeout)
      if (controller.current === abort) {
        setBusy(false)
        controller.current = null
      }
    }
  }

  async function openSaved(identifier: string) {
    if (!connection) return
    try {
      const result = ReportSchema.parse(
        await requestJson(connection.origin, '/api/reports/' + identifier, connection.token, {
          signal: AbortSignal.timeout(8000),
        }),
      )
      setReport(result)
      setQuery(result.ticker)
      setQuestion(result.question || 'Summarize the available evidence and its limitations.')
      setHistoryOpen(false)
      setError('')
    } catch {
      setError('Saved report could not be opened.')
    }
  }

  async function clearSaved() {
    if (
      !connection ||
      !window.confirm('Delete all saved research reports from this private workspace?')
    )
      return
    try {
      await requestJson(connection.origin, '/api/reports', connection.token, {
        method: 'DELETE',
        signal: AbortSignal.timeout(8000),
      })
      setSaved([])
    } catch {
      setError('Saved reports could not be deleted.')
    }
  }

  const difference =
    report?.price !== null && report?.price !== undefined && report.previous_close
      ? ((report.price - report.previous_close) / report.previous_close) * 100
      : null
  const activeTables = report?.tables.filter((table) => groups[section].includes(table.id)) || []

  return (
    <div className="workspace">
      <header className="topbar">
        <a className="brand" href={import.meta.env.BASE_URL}>
          <Activity size={23} strokeWidth={1.7} />
          <span>
            Market<span className="brand-light">Insight</span>
          </span>
        </a>
        <span className="workspace-label">RESEARCH WORKSPACE</span>
        <div className="top-actions">
          <span className={'mode-badge ' + (connection ? 'connected' : '')}>
            <span className="status-dot" />
            {connection ? 'Private API connected' : 'Synthetic reference'}
          </span>
          <button
            className="icon-button"
            title="Saved research"
            aria-label="Saved research"
            onClick={() => setHistoryOpen(true)}
          >
            <History size={18} />
          </button>
          <button
            className="icon-button"
            title="API connection"
            aria-label="API connection"
            onClick={() => {
              setError('')
              setConnectionOpen(true)
            }}
          >
            <Settings2 size={18} />
          </button>
        </div>
      </header>
      <div className="layout">
        <aside className="sidebar">
          <div className="side-heading">
            REFERENCE SET <span>03</span>
          </div>
          <nav aria-label="Reference companies">
            {samples.map((sample) => (
              <button
                key={sample.ticker}
                className={'company-item ' + (report?.ticker === sample.ticker ? 'selected' : '')}
                onClick={() => selectSample(sample)}
              >
                <span className="company-mark">
                  {sample.name
                    .split(' ')
                    .map((word) => word[0])
                    .join('')}
                </span>
                <span>
                  <strong>{sample.ticker}</strong>
                  <small>{sample.name}</small>
                </span>
                <ChevronRight size={14} />
              </button>
            ))}
          </nav>
          <div className="side-rule" />
          <div className="side-heading">OBSERVATION</div>
          <div className="integrity-item">
            <ShieldCheck size={17} />
            <span>{report?.mode === 'live' ? 'Provider evidence' : 'Synthetic dataset'}</span>
          </div>
          <div className="integrity-item">
            <Clock3 size={17} />
            <span>{report ? dateLabel(report.price_as_of) : 'Not supplied'}</span>
          </div>
          <div className="side-bottom">
            <a
              href="https://github.com/Sushant-Nemade/MarketInsight"
              target="_blank"
              rel="noreferrer"
            >
              Source & license <ArrowRight size={13} />
            </a>
            <span>GPLv3 · Reference 0.2.0</span>
          </div>
        </aside>
        <main>
          <div className="main-heading">
            <div>
              <p className="eyebrow">EQUITY WORKBENCH</p>
              <h1>Company research</h1>
            </div>
            <span className="small muted">
              {report ? dateLabel(report.created_at) : 'Reference workspace'}
            </span>
          </div>
          <form className="search-bar" onSubmit={(event) => void research(event)}>
            <button
              className="icon-button"
              type="button"
              title="Find company or ticker"
              aria-label="Find company or ticker"
              onClick={() => void lookup()}
            >
              <Search size={18} />
            </button>
            <input
              aria-label="Ticker symbol"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              maxLength={80}
              placeholder="Ticker or company"
            />
            <span className="search-divider" />
            <span className="search-mode">
              {connection ? 'Owner workspace' : 'Sample companies'}
            </span>
            <button className="command-button" disabled={busy || loading} type="submit">
              {busy ? <LoaderCircle size={16} className="spin" /> : <ArrowRight size={16} />}
              <span>{busy ? 'Researching' : 'Research'}</span>
            </button>
          </form>
          {!!matches.length && (
            <div className="lookup-results">
              {matches.map((match) => (
                <button
                  key={match.ticker}
                  onClick={() => {
                    setQuery(match.ticker)
                    setMatches([])
                  }}
                >
                  <strong>{match.ticker}</strong>
                  <span>{match.name}</span>
                  <small>{match.exchange}</small>
                  <ArrowRight size={14} />
                </button>
              ))}
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <CircleAlert size={17} />
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError('')}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {loading ? (
            <div className="loading-state" role="status">
              <LoaderCircle className="spin" />
              Loading reference evidence
            </div>
          ) : loadError ? (
            <div className="loading-state">
              <CircleAlert />
              <p>{loadError}</p>
              <button className="text-button" onClick={() => void loadSamples()}>
                Retry
              </button>
            </div>
          ) : (
            report && (
              <>
                <section className="company-overview">
                  <div className="company-identity">
                    <div className="large-mark">
                      {report.name
                        .split(' ')
                        .map((word) => word[0])
                        .slice(0, 2)
                        .join('')}
                    </div>
                    <div>
                      <div className="company-line">
                        <h2>{report.name}</h2>
                        <span className="ticker-tag">{report.ticker}</span>
                      </div>
                      <p>
                        {report.sector || 'Sector unavailable'}
                        <span className="dot-separator">·</span>
                        {report.currency || 'Currency unavailable'}
                        <span className="dot-separator">·</span>
                        <span className={report.mode === 'sample' ? 'sample-label' : 'live-label'}>
                          {report.mode === 'sample'
                            ? 'Fictional sample data'
                            : 'Provider observation'}
                        </span>
                      </p>
                    </div>
                  </div>
                  <button className="subtle-button" onClick={() => exportReport(report)}>
                    <ArrowDownToLine size={16} />
                    Export JSON
                  </button>
                </section>
                <section className="market-panel">
                  <div className="quote-row">
                    <div>
                      <span className="small muted">
                        {report.price_kind === 'historical_close'
                          ? 'Last historical close'
                          : 'Observed price'}
                      </span>
                      <div className="price-row">
                        <strong>{money(report.price)}</strong>
                        <span className="currency">{report.currency}</span>
                        {difference !== null && (
                          <span className={difference >= 0 ? 'positive' : 'negative'}>
                            {difference >= 0 ? '+' : ''}
                            {difference.toFixed(2)}%
                          </span>
                        )}
                      </div>
                      <span className="small muted">As of {dateLabel(report.price_as_of)}</span>
                    </div>
                    <div className="segmented" aria-label="Chart period">
                      {[
                        [22, '1M'],
                        [66, '3M'],
                        [126, '6M'],
                        [260, '1Y'],
                      ].map(([days, label]) => (
                        <button
                          key={days}
                          className={range === days ? 'active' : ''}
                          onClick={() => setRange(Number(days))}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <PriceChart history={report.history} range={range} />
                  <div className="metrics-grid">
                    {report.metrics.map((metric) => (
                      <div key={metric.label}>
                        <span>{metric.label}</span>
                        <strong>
                          {compact(metric.value)}
                          {metric.unit === 'x' ? 'x' : ''}
                        </strong>
                      </div>
                    ))}
                  </div>
                </section>
                <nav className="tabs" aria-label="Research sections">
                  {sections.map((value) => (
                    <button
                      key={value}
                      className={section === value ? 'active' : ''}
                      aria-current={section === value ? 'page' : undefined}
                      onClick={() => setSection(value)}
                    >
                      {labels[value]}
                    </button>
                  ))}
                </nav>
                <div className="research-grid">
                  <div className="primary-evidence">
                    {section === 'overview' ? (
                      <>
                        <section className="data-section">
                          <div className="section-title">
                            <h3>Business profile</h3>
                            <span className="small muted">Company overview</span>
                          </div>
                          <p className="body-copy">
                            {report.description ||
                              'Business profile unavailable from this provider.'}
                          </p>
                        </section>
                        <section className="data-section">
                          <div className="section-title">
                            <h3>Research notes</h3>
                            <span className="analysis-badge">
                              {report.analysis_kind === 'ai'
                                ? 'AI synthesis'
                                : report.analysis_kind === 'reference'
                                  ? 'Authored reference'
                                  : 'Evidence inventory'}
                            </span>
                          </div>
                          <p className="body-copy preserve-lines">{report.summary}</p>
                        </section>
                      </>
                    ) : section === 'news' ? (
                      <section className="data-section">
                        <div className="section-title">
                          <h3>News & disclosures</h3>
                        </div>
                        {report.news.length ? (
                          report.news.map((item) => (
                            <a
                              className="news-item"
                              key={item.url}
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <span>{item.title}</span>
                              <small>
                                {item.publisher} · {dateLabel(item.published_at)}
                              </small>
                              <ArrowRight size={14} />
                            </a>
                          ))
                        ) : (
                          <p className="empty">News unavailable for this observation.</p>
                        )}
                      </section>
                    ) : activeTables.length ? (
                      activeTables.map((table) => <FinancialTable table={table} key={table.id} />)
                    ) : (
                      <p className="empty">This section was not returned by the provider.</p>
                    )}
                    <section className="question-section">
                      <label htmlFor="research-question">Research question</label>
                      <textarea
                        id="research-question"
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        maxLength={1200}
                        rows={3}
                      />
                      <div className="question-actions">
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            checked={useAi}
                            onChange={(event) => setUseAi(event.target.checked)}
                            disabled={!connection?.ai || report.mode === 'sample'}
                          />
                          AI synthesis
                        </label>
                        {busy ? (
                          <button
                            className="subtle-button"
                            onClick={() => controller.current?.abort()}
                          >
                            Cancel
                          </button>
                        ) : (
                          <button className="subtle-button" onClick={() => void research()}>
                            Review evidence <ArrowRight size={14} />
                          </button>
                        )}
                      </div>
                    </section>
                  </div>
                  <aside className="source-panel">
                    <div className="section-title">
                      <h3>Evidence record</h3>
                      <ShieldCheck size={16} />
                    </div>
                    <span className="record-label">SOURCES</span>
                    {report.sources.map((source) => (
                      <a
                        className="source-item"
                        href={source.url}
                        key={source.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <Link2 size={14} />
                        <span>
                          {source.name}
                          <small>Observed {dateLabel(source.observed_at)}</small>
                        </span>
                      </a>
                    ))}
                    <div className="record-divider" />
                    <span className="record-label">LIMITATIONS</span>
                    {report.limitations.map((limit) => (
                      <p className="limitation" key={limit}>
                        {limit}
                      </p>
                    ))}
                    <div className="record-divider" />
                    <p className="record-foot">
                      <Clock3 size={14} />
                      {report.history.length} price observations
                    </p>
                  </aside>
                </div>
                <footer className="workspace-footer">
                  <span>Educational research. Not investment advice.</span>
                  <a href="https://github.com/Sushant-Nemade/MarketInsight/blob/main/NOTICE.md">
                    Attribution & source
                  </a>
                </footer>
              </>
            )
          )}
        </main>
      </div>
      {connectionOpen && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="connection-title"
          >
            <div className="section-title">
              <h2 id="connection-title">Private API connection</h2>
              <button
                className="icon-button"
                aria-label="Close connection"
                onClick={() => {
                  setConnectionOpen(false)
                  setTokenDraft('')
                }}
              >
                <X size={18} />
              </button>
            </div>
            <form onSubmit={(event) => void connect(event)}>
              <label>
                API origin
                <input
                  type="url"
                  required
                  value={originDraft}
                  onChange={(event) => setOriginDraft(event.target.value)}
                />
              </label>
              <label>
                Access token
                <input
                  type="password"
                  autoComplete="off"
                  required
                  minLength={32}
                  maxLength={256}
                  value={tokenDraft}
                  onChange={(event) => setTokenDraft(event.target.value)}
                />
              </label>
              {error && (
                <p className="dialog-error" role="alert">
                  {error}
                </p>
              )}
              <div className="modal-actions">
                {connection && (
                  <button
                    className="subtle-button"
                    type="button"
                    onClick={() => {
                      disconnect()
                      setConnectionOpen(false)
                    }}
                  >
                    <LogOut size={16} />
                    Disconnect
                  </button>
                )}
                <button className="command-button" type="submit">
                  <Check size={16} />
                  Connect
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
      {historyOpen && (
        <div className="modal-backdrop">
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="history-title"
          >
            <div className="section-title">
              <h2 id="history-title">Saved research</h2>
              <button
                className="icon-button"
                aria-label="Close saved research"
                onClick={() => setHistoryOpen(false)}
              >
                <X size={18} />
              </button>
            </div>
            {saved.length ? (
              <>
                <div className="saved-list">
                  {saved.map((item) => (
                    <button key={item.id} onClick={() => void openSaved(item.id)}>
                      <FileText size={17} />
                      <strong>{item.ticker}</strong>
                      <span>{dateLabel(item.created_at)}</span>
                      <ChevronRight size={14} />
                    </button>
                  ))}
                </div>
                <button className="subtle-button danger" onClick={() => void clearSaved()}>
                  <Trash2 size={15} />
                  Clear saved reports
                </button>
              </>
            ) : (
              <div className="empty">
                {connection ? 'No saved reports.' : 'No private API connected.'}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  )
}
