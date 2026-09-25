export type Product = {
  id: string
  title: string
  description: string
  source_category: string
  brand: string
}
export type Supplier = { id: string; name: string; region: string; products: Product[] }
export type Category = { id: string; path: string; description: string; retrieval_score?: number }
export type Market = {
  id: string
  name: string
  region: string
  version: string
  categories: Category[]
}
export type Mapping = {
  id: string
  supplier_id: string
  supplier_name: string
  marketplace_id: string
  marketplace_name: string
  product: Product
  taxonomy: Market
  category_id?: string
  probabilities?: Record<string, number>
  candidates: Category[]
  baseline_id: string
  model_ms?: number
  status: string
  mode: string
  metadata?: Record<string, string | number>
  error?: string
  review?: { category_id: string; note: string; created_at: string } | null
}
export type Job = {
  id: string
  status: string
  total: number
  completed: number
  errors: number
  error?: string
}
export type Summary = {
  decisions: number
  accuracy: number
  baseline_accuracy: number
  lift: number
  shortlist_recall: number
  unmatched_recall: number
  p50_model_ms: number
  p95_model_ms: number
  passed: boolean
  gates: Record<string, boolean>
  slices: Record<string, { count: number; accuracy: number }>
}
export type Report = {
  created_at: string
  methodology: string
  metadata: Record<string, string | number>
  summary: Summary
  rows: {
    case_id: string
    marketplace_id: string
    category_id: string
    expected_id: string
    product: Product
    taxonomy: Market
    slice: string
  }[]
}
export type State = {
  suppliers: Supplier[]
  marketplaces: Market[]
  mappings: Mapping[]
  jobs: Job[]
  live_enabled: boolean
  recording: Omit<Report, 'rows'>
}
