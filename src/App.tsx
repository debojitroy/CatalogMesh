import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Box,
  Boxes,
  Check,
  CheckCheck,
  ChevronDown,
  ChevronRight,
  Coffee,
  Cpu,
  FlaskConical,
  GitBranch,
  Globe2,
  Headphones,
  Layers3,
  LayoutGrid,
  LoaderCircle,
  Package,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  Workflow,
  Wrench,
  X,
} from 'lucide-react'
import { api } from './api'
import type { Mapping, Market, Product, Report, State, Supplier } from './types'

const percent = (n: number) => `${(n * 100).toFixed(1)}%`
const leaf = (path: string) => path.split(' / ').at(-1)
const categoryName = (market: Market, id?: string) =>
  id === 'unmatched'
    ? 'Unresolved: no fit or insufficient information'
    : market.categories.find((c) => c.id === id)?.path || 'No decision'
const initials = (name: string) =>
  name
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
const nav = [
  { id: 'overview', name: 'Connections', icon: LayoutGrid },
  { id: 'ledger', name: 'Mapping ledger', icon: GitBranch },
  { id: 'taxonomies', name: 'Taxonomies', icon: Layers3 },
  { id: 'evaluation', name: 'Evaluation', icon: FlaskConical },
] as const
type View = (typeof nav)[number]['id']

function ProductIcon({ supplier }: { supplier: string }) {
  const Icon = supplier === 'northline' ? Headphones : supplier === 'homestead' ? Coffee : Wrench
  return (
    <span className={`product-icon ${supplier}`}>
      <Icon size={24} strokeWidth={1.4} />
    </span>
  )
}

function Dialog({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string
  onClose: () => void
  children: ReactNode
  wide?: boolean
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    ref.current?.showModal()
    return () => ref.current?.close()
  }, [])
  return (
    <dialog className={wide ? 'wide' : ''} ref={ref} aria-label={title} onCancel={onClose}>
      <div className="dialog-head">
        <h2>{title}</h2>
        <button className="icon-button" aria-label="Close dialog" onClick={onClose}>
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  )
}

function ImportDialog({
  kind,
  existing,
  onClose,
  onSaved,
}: {
  kind: 'supplier' | 'marketplace'
  existing?: Market
  onClose: () => void
  onSaved: () => void
}) {
  const example =
    kind === 'supplier'
      ? {
          id: 'new-supplier',
          name: 'New supplier',
          region: 'Imported feed',
          products: [
            {
              id: 'SKU-001',
              title: 'Product title',
              description: 'Describe the actual item being sold.',
              source_category: 'Supplier category',
              brand: 'Brand',
            },
          ],
        }
      : existing
        ? { ...existing, version: `${existing.version}-revision` }
        : {
            id: 'new-market',
            name: 'New marketplace',
            region: 'Custom taxonomy',
            version: '1',
            categories: [
              {
                id: 'CAT-1',
                path: 'Electronics / Headphones',
                description: 'Complete headphones and earbuds.',
              },
              {
                id: 'CAT-2',
                path: 'Electronics / Accessories',
                description:
                  'Replacement ear tips, protective cases and other headphone accessories.',
              },
            ],
          }
  const [text, setText] = useState(JSON.stringify(example, null, 2))
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  async function save() {
    setSaving(true)
    setError('')
    try {
      await api(kind === 'supplier' ? '/suppliers' : '/marketplaces', JSON.parse(text))
      onSaved()
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }
  return (
    <Dialog
      title={existing ? `Revise ${existing.name}` : `Connect a ${kind}`}
      onClose={onClose}
      wide
    >
      <p className="dialog-intro">
        {kind === 'supplier'
          ? 'Bring your product feed as JSON. Every connected marketplace becomes a destination.'
          : 'Supply destination category IDs, paths and definitions. Laya uses the definitions to select each product’s category.'}{' '}
        Imported or changed data requires live Laya.
      </p>
      <label className="file-picker">
        <Upload size={16} /> Load JSON file
        <input
          type="file"
          accept=".json,application/json"
          onChange={async (e) => {
            const file = e.target.files?.[0]
            if (!file) return
            if (file.size > 3_000_000) {
              setError('File exceeds 3 MB')
              return
            }
            setText(await file.text())
          }}
        />
      </label>
      <label className="field">
        Catalog definition
        <textarea
          className="code-editor"
          value={text}
          onChange={(e) => setText(e.target.value)}
          spellCheck={false}
        />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="dialog-actions">
        <button className="secondary" onClick={onClose}>
          Cancel
        </button>
        <button className="primary" disabled={saving} onClick={save}>
          {saving ? 'Saving…' : existing ? 'Save taxonomy revision' : 'Connect catalog'}
          <ArrowRight size={16} />
        </button>
      </div>
    </Dialog>
  )
}

function DecisionDialog({
  row,
  onClose,
  onReviewed,
}: {
  row: Mapping
  onClose: () => void
  onReviewed: () => void
}) {
  const [category, setCategory] = useState(
    row.review?.category_id || row.category_id || 'unmatched',
  )
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const ranked = Object.entries(row.probabilities || {}).sort((a, b) => b[1] - a[1])
  async function review() {
    setSaving(true)
    setError('')
    try {
      await api(`/mappings/${row.id}/review`, { category_id: category, note })
      onReviewed()
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }
  return (
    <Dialog title="Inside the Laya decision" onClose={onClose} wide>
      <div className="decision-summary">
        <ProductIcon supplier={row.supplier_id} />
        <div>
          <span className="mono">
            {row.product.id} · {row.supplier_name}
          </span>
          <h3>{row.product.title}</h3>
        </div>
      </div>
      <p>{row.product.description}</p>
      <div className="source-line">
        <span>Supplier category</span>
        <strong>{row.product.source_category || 'Not supplied'}</strong>
      </div>
      <div className="source-line">
        <span>Destination</span>
        <strong>
          {row.marketplace_name} · {row.taxonomy.version}
        </strong>
      </div>
      {row.error ? (
        <p className="error">{row.error}</p>
      ) : (
        <>
          <div className="decision-choice">
            <Cpu size={22} />
            <div>
              <small>Laya selected</small>
              <strong>{categoryName(row.taxonomy, row.category_id)}</strong>
            </div>
            <span>{row.model_ms?.toFixed(1)} ms</span>
          </div>
          <div className="section-heading">
            <h3>Candidate distribution</h3>
            <span>{row.mode === 'recorded' ? 'Recorded model output' : 'Live model output'}</span>
          </div>
          <div className="probabilities">
            {ranked.map(([id, value]) => (
              <div key={id}>
                <div>
                  <span>{leaf(categoryName(row.taxonomy, id))}</span>
                  <strong>{percent(value)}</strong>
                </div>
                <div className="bar-track">
                  <div
                    className={id === row.category_id ? 'chosen' : ''}
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          <p className="fineprint">
            Probabilities apply to the retrieved candidates plus “unmatched”. They are not
            calibrated estimates of mapping correctness. Every result is a proposal for review.
          </p>
          <div className="baseline-note">
            <Search size={16} />
            <span>
              Lexical baseline selected{' '}
              <strong>{leaf(categoryName(row.taxonomy, row.baseline_id))}</strong>.
            </span>
          </div>
          <details>
            <summary>Model & decision provenance</summary>
            <pre>{JSON.stringify(row.metadata, null, 2)}</pre>
            <a href={`/api/mappings/${row.id}/export`} className="text-link">
              Download full decision JSON <ArrowDownToLine size={14} />
            </a>
          </details>
          {row.review && (
            <div className="review-note">
              <CheckCheck size={16} />
              <span>
                Previous review: {categoryName(row.taxonomy, row.review.category_id)}.{' '}
                {row.review.note}
              </span>
            </div>
          )}
          <div className="review-form">
            <h3>Merchandiser review</h3>
            <label className="field">
              Confirm or correct the category
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {row.taxonomy.categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.path}
                  </option>
                ))}
                <option value="unmatched">Unresolved / no suitable category</option>
              </select>
            </label>
            <label className="field">
              Review note
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Why is this the right destination?"
              />
            </label>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <span className="fineprint">The original model output stays unchanged.</span>
            <button
              className="primary"
              disabled={saving || note.trim().length < 2}
              onClick={review}
            >
              Save review <Check size={16} />
            </button>
          </div>
        </>
      )}
    </Dialog>
  )
}

function Evaluation({ report }: { report: Report | null }) {
  if (!report?.summary) return <div className="empty">No recorded evaluation is available.</div>
  const s = report.summary
  const failures = report.rows.filter((r) => r.category_id !== r.expected_id)
  return (
    <>
      <div className="page-heading compact">
        <div>
          <span className="eyebrow">EVIDENCE, BEFORE AUTOMATION</span>
          <h1>Does the mapping hold up?</h1>
          <p>Real model outputs, fixed examples, visible failures.</p>
        </div>
        <a className="secondary" href="/api/evaluation" download="catalogmesh-evaluation.json">
          <ArrowDownToLine size={16} /> Full eval report
        </a>
      </div>
      <div className={`gate-banner ${s.passed ? 'pass' : 'fail'}`}>
        <ShieldCheck size={22} />
        <div>
          <strong>{s.passed ? 'Pilot quality gates passed' : 'Pilot quality gate not met'}</strong>
          <p>
            {s.passed
              ? 'These results meet the declared pilot bars. They do not establish production accuracy.'
              : 'The current model is below a declared quality bar. Keep mappings under human review.'}
          </p>
        </div>
        <span>{s.decisions} decisions</span>
      </div>
      <div className="metrics evaluation-metrics">
        <Metric
          label="LAYA ACCURACY"
          value={percent(s.accuracy)}
          detail="Exact destination category"
        />
        <Metric
          label="LEXICAL BASELINE"
          value={percent(s.baseline_accuracy)}
          detail="Same product and shortlist"
        />
        <Metric
          label="LAYA LIFT"
          value={`${s.lift >= 0 ? '+' : ''}${(s.lift * 100).toFixed(1)} pp`}
          detail="Over lexical top candidate"
        />
        <Metric
          label="SHORTLIST RECALL"
          value={percent(s.shortlist_recall)}
          detail="For products with a valid category"
        />
      </div>
      <div className="evaluation-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Performance by challenge</h2>
            <span>Authored evaluation</span>
          </div>
          <div className="slice-list">
            {Object.entries(s.slices).map(([name, slice]) => (
              <div key={name}>
                <span>{name.replaceAll('-', ' ')}</span>
                <div className="bar-track">
                  <div className="chosen" style={{ width: `${slice.accuracy * 100}%` }} />
                </div>
                <strong>{percent(slice.accuracy)}</strong>
                <small>{slice.count} decisions</small>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Regression gates</h2>
            <FlaskConical size={17} />
          </div>
          <div className="gate-list">
            {Object.entries(s.gates).map(([name, passed]) => (
              <div key={name}>
                <span className={passed ? 'green' : 'red'}>
                  {passed ? <Check size={17} /> : <X size={17} />}
                </span>
                <span>{name.replaceAll('_', ' ')}</span>
                <strong>{passed ? 'PASS' : 'FAIL'}</strong>
              </div>
            ))}
          </div>
          <div className="timing">
            <span>Warm model call · p50 / p95</span>
            <strong>
              {s.p50_model_ms.toFixed(1)} / {s.p95_model_ms.toFixed(1)} ms
            </strong>
            <small>
              {report.metadata.hardware} · includes tokenization and output decoding; excludes
              network and retrieval.
            </small>
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Failure explorer</h2>
          <span>{failures.length} incorrect decisions retained</span>
        </div>
        <div className="table-scroll">
          <table className="ledger">
            <thead>
              <tr>
                <th>Product</th>
                <th>Marketplace</th>
                <th>Laya selected</th>
                <th>Expected category</th>
              </tr>
            </thead>
            <tbody>
              {failures.map((r) => (
                <tr key={`${r.case_id}-${r.marketplace_id}`}>
                  <td>
                    <strong>{r.product.title}</strong>
                    <small>
                      {r.case_id} · {r.slice}
                    </small>
                  </td>
                  <td>{r.taxonomy.name}</td>
                  <td className="red">{leaf(categoryName(r.taxonomy, r.category_id))}</td>
                  <td>{leaf(categoryName(r.taxonomy, r.expected_id))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <p className="methodology">
        <BookOpen size={18} />
        <span>
          {report.methodology} This set was used to diagnose the first adapter failure; it is now a
          regression suite, not an untouched test set. Live reruns write candidate reports and must
          be compared before updating the baseline.
        </span>
      </p>
    </>
  )
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string
  value: string | number
  detail: string
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  )
}

export default function App() {
  const [state, setState] = useState<State | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [view, setView] = useState<View>('overview')
  const [mode, setMode] = useState<'recorded' | 'live'>('recorded')
  const [selectedSupplier, setSupplier] = useState('northline')
  const [selectedProduct, setProduct] = useState('NL-103')
  const [activeMarket, setActiveMarket] = useState('harbor')
  const [importing, setImporting] = useState<'supplier' | 'marketplace' | null>(null)
  const [editing, setEditing] = useState<Market | undefined>()
  const [inspecting, setInspecting] = useState<Mapping | null>(null)
  const [error, setError] = useState('')
  const [pending, setPending] = useState(false)
  const [search, setSearch] = useState('')
  const [notice, setNotice] = useState('')

  async function refresh() {
    setState(await api<State>('/state'))
  }
  useEffect(() => {
    let stopped = false
    Promise.all([api<State>('/state'), api<Report>('/evaluation')])
      .then(([s, r]) => {
        if (!stopped) {
          setState(s)
          setReport(r)
        }
      })
      .catch((e) => {
        if (!stopped) setError(e.message)
      })
    return () => {
      stopped = true
    }
  }, [])
  const running = state?.jobs.some((j) => j.status === 'running' || j.status === 'queued') || false
  useEffect(() => {
    if (!running) return
    const id = setInterval(() => refresh().catch((e) => setError(e.message)), 600)
    return () => clearInterval(id)
  }, [running])
  const latest = useMemo(() => {
    const seen = new Set<string>()
    return (state?.mappings || []).filter((row) => {
      const key = `${row.supplier_id}:${row.product.id}:${row.marketplace_id}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  }, [state])
  const supplier = state?.suppliers.find((s) => s.id === selectedSupplier) || state?.suppliers[0]
  const product = supplier?.products.find((p) => p.id === selectedProduct) || supplier?.products[0]
  const markets = state?.marketplaces || []
  const getRow = (sid: string, pid: string, mid: string) =>
    latest.find((r) => r.supplier_id === sid && r.product.id === pid && r.marketplace_id === mid)
  const stale = (row: Mapping) => {
    const currentMarket = markets.find((m) => m.id === row.marketplace_id)
    const p = state?.suppliers
      .find((s) => s.id === row.supplier_id)
      ?.products.find((p) => p.id === row.product.id)
    return (
      currentMarket?.version !== row.taxonomy.version ||
      !p ||
      ['title', 'description', 'source_category', 'brand'].some(
        (k) => p[k as keyof Product] !== row.product[k as keyof Product],
      )
    )
  }
  async function map(supplierIds?: string[], marketIds?: string[]) {
    if (!state) return
    setError('')
    setPending(true)
    setNotice('')
    try {
      await api('/jobs', {
        supplier_ids: supplierIds || state.suppliers.map((s) => s.id),
        marketplace_ids: marketIds || markets.map((m) => m.id),
        mode,
      })
      await refresh()
      setNotice(
        mode === 'recorded'
          ? 'Loaded real recorded Laya decisions. Open any mapping to inspect its provenance.'
          : 'Live Laya mapping started.',
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setPending(false)
    }
  }
  function chooseSupplier(s: Supplier) {
    setSupplier(s.id)
    setProduct(s.products[0].id)
  }
  const filtered = latest.filter((r) =>
    `${r.product.title} ${r.product.id} ${r.marketplace_name} ${r.supplier_name}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  )
  const job = state?.jobs[0]

  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="CatalogMesh home">
          <Box size={29} strokeWidth={1.7} />
          <span>
            catalog<span>mesh</span>
            <i />
          </span>
        </a>
        <div className="workspace">
          <span className="workspace-avatar">M</span>
          <div>
            Meridian Reseller<small>DEMO WORKSPACE</small>
          </div>
          <ChevronDown size={14} />
        </div>
        <span className="nav-label">WORKSPACE</span>
        <nav>
          {nav.map(({ id, name, icon: Icon }) => (
            <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>
              <Icon size={18} />
              {name}
              {id === 'evaluation' && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <Workflow size={25} strokeWidth={1.4} />
          <h3>
            Many to many.
            <br />
            One workspace.
          </h3>
          <p>Connect any imported supplier to any imported marketplace taxonomy.</p>
          <button onClick={() => setImporting('marketplace')}>
            Add a destination <ArrowUpRight size={14} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <a href="https://github.com/debojitroy/CatalogMesh" target="_blank" rel="noreferrer">
            <BookOpen size={16} /> Project & documentation <ArrowUpRight size={13} />
          </a>
          <div>
            <span className="status-dot" /> OPEN SOURCE <span>v0.1.0</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div>
            <span>Meridian workspace</span>
            <ChevronRight size={13} />
            <strong>{nav.find((n) => n.id === view)?.name}</strong>
          </div>
          <div className="model-pill">
            <span className="status-dot" />
            <Cpu size={14} /> Laya powered <span className="pill-divider" />{' '}
            {mode === 'recorded' ? 'Recorded demo' : 'Live inference'}
          </div>
        </header>
        <main>
          {error && (
            <div className="error global-error" role="alert">
              <span>{error}</span>
              <button onClick={() => setError('')} aria-label="Dismiss error">
                <X size={17} />
              </button>
            </div>
          )}
          {!state ? (
            <div className="loading">
              <LoaderCircle className="spin" /> Loading your catalog workspace…
            </div>
          ) : (
            <>
              {view === 'overview' && (
                <>
                  <div className="page-heading">
                    <div>
                      <span className="eyebrow">
                        <span /> THE CATALOG CONNECTION LAYER
                      </span>
                      <h1>
                        Every catalog.
                        <br />
                        <em>Every destination.</em>
                      </h1>
                      <p>
                        Turn supplier language into marketplace categories.
                        <br />
                        Laya makes the semantic match. You stay in control.
                      </p>
                    </div>
                    <div className="hero-network" aria-hidden="true">
                      <div className="network-column">
                        <span>
                          <Package size={18} />
                        </span>
                        <span>
                          <Boxes size={18} />
                        </span>
                        <span>
                          <Package size={18} />
                        </span>
                      </div>
                      <div className="network-lines" />
                      <div className="network-core">
                        <Box size={34} />
                        <small>LAYA</small>
                      </div>
                      <div className="network-lines right" />
                      <div className="network-column">
                        <span>
                          <Globe2 size={18} />
                        </span>
                        <span>
                          <Globe2 size={18} />
                        </span>
                        <span>
                          <Globe2 size={18} />
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="metrics">
                    <Metric
                      label="CONNECTED SUPPLIERS"
                      value={state.suppliers.length.toString().padStart(2, '0')}
                      detail="Independent source catalogs"
                    />
                    <Metric
                      label="MARKETPLACES"
                      value={markets.length.toString().padStart(2, '0')}
                      detail="Distinct destination taxonomies"
                    />
                    <Metric
                      label="POSSIBLE CONNECTIONS"
                      value={state.suppliers.length * markets.length}
                      detail="Every supplier × every marketplace"
                    />
                    <Metric
                      label="CATALOG PRODUCTS"
                      value={state.suppliers.reduce((n, s) => n + s.products.length, 0)}
                      detail="Authored sample listings + imports"
                    />
                  </div>
                  <section className="panel connection-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>The connection matrix</h2>
                        <p>Choose a route. Inspect what each marketplace receives.</p>
                      </div>
                      <button className="text-button" onClick={() => setImporting('marketplace')}>
                        <Plus size={15} /> Connect marketplace
                      </button>
                    </div>
                    <div className="matrix-scroll">
                      <table className="matrix">
                        <thead>
                          <tr>
                            <th>
                              SUPPLIER <ArrowRight size={12} /> DESTINATION
                            </th>
                            {markets.map((m, i) => (
                              <th key={m.id}>
                                <div>
                                  <span className={`market-icon market-${i % 3}`}>
                                    <Globe2 size={16} />
                                  </span>
                                  <span>
                                    {m.name}
                                    <small>{m.region}</small>
                                  </span>
                                </div>
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {state.suppliers.map((s) => (
                            <tr key={s.id}>
                              <th>
                                <button onClick={() => chooseSupplier(s)}>
                                  <span className={`supplier-avatar ${s.id}`}>
                                    {initials(s.name)}
                                  </span>
                                  <span>
                                    {s.name}
                                    <small>
                                      {s.products.length} products · {s.region.split(' · ').at(-1)}
                                    </small>
                                  </span>
                                </button>
                              </th>
                              {markets.map((m) => {
                                const rows = latest.filter(
                                  (r) =>
                                    r.supplier_id === s.id &&
                                    r.marketplace_id === m.id &&
                                    !stale(r),
                                )
                                const mapped = rows.filter((r) => r.status === 'proposed').length
                                return (
                                  <td key={m.id}>
                                    <button
                                      className={`matrix-cell ${supplier?.id === s.id && activeMarket === m.id ? 'selected' : ''}`}
                                      onClick={() => {
                                        chooseSupplier(s)
                                        setActiveMarket(m.id)
                                      }}
                                    >
                                      <span className="cell-top">
                                        <span
                                          className={`status-dot ${rows.length ? '' : 'muted-dot'}`}
                                        />
                                        {rows.length ? `${mapped} proposed` : 'Ready to map'}
                                        <ArrowUpRight size={14} />
                                      </span>
                                      <span className="cell-detail">
                                        {rows.length
                                          ? `${rows.length - mapped} unresolved / errors`
                                          : `${s.products.length} products → ${m.categories.length} categories`}
                                      </span>
                                      <div className="cell-track">
                                        <span
                                          style={{
                                            width: `${(rows.length / s.products.length) * 100}%`,
                                          }}
                                        />
                                      </div>
                                    </button>
                                  </td>
                                )
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="matrix-footer">
                      <button className="text-button" onClick={() => setImporting('supplier')}>
                        <Plus size={15} /> Connect supplier
                      </button>
                      <span>
                        <span className="status-dot" /> Model proposals · review before export
                      </span>
                    </div>
                  </section>
                  <div className="run-toolbar">
                    <div>
                      <label className="inline-label">
                        Decision source
                        <select
                          aria-label="Decision source"
                          value={mode}
                          onChange={(e) => setMode(e.target.value as typeof mode)}
                        >
                          <option value="recorded">Recorded Laya runs</option>
                          <option value="live" disabled={!state.live_enabled}>
                            Live Laya{!state.live_enabled ? ' · configure worker' : ''}
                          </option>
                        </select>
                      </label>
                      <small>
                        {mode === 'recorded'
                          ? 'Genuine model outputs for the sample catalog. No GPU needed to explore.'
                          : 'Products and destination candidates are evaluated by the local Laya worker.'}
                      </small>
                    </div>
                    <button className="primary" disabled={pending || running} onClick={() => map()}>
                      {pending || running ? (
                        <LoaderCircle className="spin" size={17} />
                      ) : (
                        <Sparkles size={17} />
                      )}
                      {pending || running
                        ? `Mapping ${job?.completed || 0}/${job?.total || '…'}`
                        : 'Map all connections'}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                  {notice && (
                    <div className="notice" role="status">
                      <Check size={16} />
                      {notice}
                    </div>
                  )}
                  {job?.error && <p className="error">{job.error}</p>}
                  {supplier && product && (
                    <section className="fanout panel">
                      <div className="panel-heading">
                        <div>
                          <h2>One product. Multiple destinations.</h2>
                          <p>Follow the meaning across independent category systems.</p>
                        </div>
                        <button
                          className="text-button"
                          disabled={pending || running}
                          onClick={() => map([supplier.id], [activeMarket])}
                        >
                          Map selected route <ArrowRight size={15} />
                        </button>
                      </div>
                      <div className="fanout-body">
                        <div className="source-product">
                          <div className="section-kicker">01 / SUPPLIER PRODUCT</div>
                          <label className="field">
                            <span className="sr-only">Choose supplier</span>
                            <select
                              aria-label="Choose supplier"
                              value={supplier.id}
                              onChange={(e) =>
                                chooseSupplier(
                                  state.suppliers.find((s) => s.id === e.target.value)!,
                                )
                              }
                            >
                              {state.suppliers.map((s) => (
                                <option key={s.id} value={s.id}>
                                  {s.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="field">
                            <span className="sr-only">Choose product</span>
                            <select
                              aria-label="Choose product"
                              value={product.id}
                              onChange={(e) => setProduct(e.target.value)}
                            >
                              {supplier.products.map((p) => (
                                <option key={p.id} value={p.id}>
                                  {p.id} · {p.title}
                                </option>
                              ))}
                            </select>
                          </label>
                          <ProductIcon supplier={supplier.id} />
                          <span className="sku">
                            {product.id} / {product.brand}
                          </span>
                          <h3>{product.title}</h3>
                          <p>{product.description}</p>
                          <div className="supplier-category">
                            <span>SUPPLIER CATEGORY</span>
                            <strong>{product.source_category}</strong>
                          </div>
                        </div>
                        <div className="semantic-bridge">
                          <div>
                            <Cpu size={23} />
                            <span>LAYA</span>
                          </div>
                          <small>
                            Candidate categories in.
                            <br />
                            Semantic choice out.
                          </small>
                        </div>
                        <div className="destinations">
                          <div className="section-kicker">02 / DESTINATION-SPECIFIC DECISIONS</div>
                          {markets.map((m, i) => {
                            const row = getRow(supplier.id, product.id, m.id)
                            return (
                              <button
                                key={m.id}
                                className={`destination ${m.id === activeMarket ? 'focused' : ''}`}
                                disabled={!row}
                                onClick={() => row && setInspecting(row)}
                              >
                                <div className="destination-top">
                                  <span className={`market-icon market-${i % 3}`}>
                                    <Globe2 size={16} />
                                  </span>
                                  <strong>{m.name}</strong>
                                  <span>
                                    {row
                                      ? row.mode === 'recorded'
                                        ? 'RECORDED'
                                        : 'LIVE'
                                      : 'AWAITING RUN'}
                                  </span>
                                </div>
                                <p>
                                  {row
                                    ? categoryName(
                                        row.taxonomy,
                                        row.review?.category_id || row.category_id,
                                      )
                                    : 'Run a mapping to see Laya’s category choice.'}
                                </p>
                                <div className="destination-bottom">
                                  {row ? (
                                    <>
                                      <span>
                                        {stale(row)
                                          ? 'Catalog changed · re-map needed'
                                          : row.review
                                            ? 'Reviewed by merchandiser'
                                            : row.status === 'error'
                                              ? 'Inference error'
                                              : row.category_id === 'unmatched'
                                                ? 'Unresolved · needs review'
                                                : `${row.model_ms?.toFixed(1)} ms model call`}
                                      </span>
                                      <span>
                                        Inspect decision <ArrowUpRight size={13} />
                                      </span>
                                    </>
                                  ) : (
                                    <span>
                                      {m.categories.length} categories · taxonomy {m.version}
                                    </span>
                                  )}
                                </div>
                              </button>
                            )
                          })}
                        </div>
                      </div>
                    </section>
                  )}
                </>
              )}
              {view === 'ledger' && (
                <>
                  <div className="page-heading compact">
                    <div>
                      <span className="eyebrow">EVERY DECISION HAS A RECORD</span>
                      <h1>Mapping ledger</h1>
                      <p>Inspect proposals, record corrections, and export destination mappings.</p>
                    </div>
                    <a className="secondary" href="/api/export">
                      <ArrowDownToLine size={16} /> Export CSV
                    </a>
                  </div>
                  <div className="searchbar">
                    <Search size={17} />
                    <input
                      aria-label="Search mappings"
                      placeholder="Search product, supplier or marketplace…"
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                    />
                    <span>{filtered.length} current decisions</span>
                  </div>
                  <section className="panel">
                    <div className="table-scroll">
                      <table className="ledger">
                        <thead>
                          <tr>
                            <th>Product</th>
                            <th>Destination</th>
                            <th>Category</th>
                            <th>Status</th>
                            <th>Source</th>
                            <th />
                          </tr>
                        </thead>
                        <tbody>
                          {filtered.map((row) => (
                            <tr key={row.id}>
                              <td>
                                <strong>{row.product.title}</strong>
                                <small>
                                  {row.product.id} · {row.supplier_name}
                                </small>
                              </td>
                              <td>
                                {row.marketplace_name}
                                <small>Taxonomy {row.taxonomy.version}</small>
                              </td>
                              <td>
                                {leaf(
                                  categoryName(
                                    row.taxonomy,
                                    row.review?.category_id || row.category_id,
                                  ),
                                )}
                              </td>
                              <td>
                                <span className={`tag ${row.review ? 'success' : ''}`}>
                                  {stale(row) ? 'Stale' : row.review ? 'Reviewed' : row.status}
                                </span>
                              </td>
                              <td>{row.mode === 'recorded' ? 'Recorded Laya' : 'Live Laya'}</td>
                              <td>
                                <button
                                  className="icon-button"
                                  aria-label={`Inspect ${row.product.id} for ${row.marketplace_name}`}
                                  onClick={() => setInspecting(row)}
                                >
                                  <ArrowUpRight size={17} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {!filtered.length && (
                      <div className="empty">
                        <GitBranch size={28} />
                        <h3>Your mapping history starts here.</h3>
                        <p>Run a connection to record its Laya decisions.</p>
                        <button className="primary" onClick={() => setView('overview')}>
                          Open connections <ArrowRight size={15} />
                        </button>
                      </div>
                    )}
                  </section>
                </>
              )}
              {view === 'taxonomies' && (
                <>
                  <div className="page-heading compact">
                    <div>
                      <span className="eyebrow">INDEPENDENT DEFINITIONS. SHARED WORKSPACE.</span>
                      <h1>Your destinations</h1>
                      <p>Category paths and definitions tell Laya what each marketplace means.</p>
                    </div>
                    <button className="primary" onClick={() => setImporting('marketplace')}>
                      <Plus size={16} /> Connect marketplace
                    </button>
                  </div>
                  <div className="taxonomy-grid">
                    {markets.map((m, i) => (
                      <section className="panel taxonomy" key={m.id}>
                        <div className="taxonomy-head">
                          <span className={`market-icon market-${i % 3}`}>
                            <Globe2 size={20} />
                          </span>
                          <div>
                            <h2>{m.name}</h2>
                            <p>{m.region}</p>
                          </div>
                          <span className="tag">{m.version}</span>
                        </div>
                        <div className="taxonomy-categories">
                          {m.categories.map((c) => (
                            <details key={c.id}>
                              <summary>
                                <GitBranch size={14} />
                                {c.path}
                                <span>{c.id}</span>
                              </summary>
                              <p>{c.description}</p>
                            </details>
                          ))}
                        </div>
                        <button
                          className="text-button"
                          onClick={() => {
                            setEditing(m)
                            setImporting('marketplace')
                          }}
                        >
                          Revise definitions <ArrowRight size={15} />
                        </button>
                      </section>
                    ))}
                  </div>
                  <div className="explanation">
                    <Layers3 size={24} />
                    <div>
                      <h3>A new taxonomy creates new mapping decisions.</h3>
                      <p>
                        Editing definitions requires a new version. Earlier decisions remain
                        inspectable; changed routes need live re-evaluation. The sample marketplaces
                        are fictional and are not commercial marketplace integrations.
                      </p>
                    </div>
                  </div>
                </>
              )}
              {view === 'evaluation' && <Evaluation report={report} />}
              <footer>
                <span>
                  <ShieldCheck size={14} /> Real Laya decisions. Authored catalogs. Reviewable
                  mappings.
                </span>
                <button onClick={() => setView('evaluation')}>
                  See the evidence <ArrowRight size={14} />
                </button>
              </footer>
            </>
          )}
        </main>
      </div>
      {importing && (
        <ImportDialog
          kind={importing}
          existing={editing}
          onClose={() => {
            setImporting(null)
            setEditing(undefined)
          }}
          onSaved={() => refresh().catch((e) => setError(e.message))}
        />
      )}
      {inspecting && (
        <DecisionDialog
          row={inspecting}
          onClose={() => setInspecting(null)}
          onReviewed={() => refresh().catch((e) => setError(e.message))}
        />
      )}
    </div>
  )
}
