import { useEffect, useMemo, useRef, useState } from 'react'
import mermaid from 'mermaid'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Code2,
  FileJson,
  GitBranch,
  ScanLine,
  Info,
  LockKeyhole,
  Network,
  Play,
  RefreshCw,
  ShieldCheck,
  Terminal,
  XCircle,
} from 'lucide-react'
import { rolePermissions, roles } from './config/rolePermissions'
import { scenarios } from './config/scenarios'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const tabs = [
  { id: 'monitor', label: 'Pipeline Monitor', icon: Activity },
  { id: 'xray', label: 'Execution Trace', icon: ScanLine },
  { id: 'raw', label: 'Raw Data', icon: FileJson },
  { id: 'theory', label: 'Architecture & Theory', icon: Network },
  { id: 'comparison', label: 'API Comparison', icon: GitBranch },
]

function MermaidDiagram() {
  const [svg, setSvg] = useState('')

  useEffect(() => {
    let active = true
    mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict' })
    mermaid.render('secure-bi-architecture', `
      flowchart LR
        U[User / Red Team] --> API[FastAPI API]
        API --> RBAC[RBAC + Schema Filter]
        RBAC --> LLM[Gemini SQL Planner]
        LLM --> AST[SQL AST Guardrail]
        AST -->|blocked| REF[Reflexion Feedback]
        REF --> LLM
        AST -->|passed| MCP[Trino MCP]
        MCP --> TAINT[Taint Filter]
        TAINT --> OUT[Safe Answer]
    `).then(({ svg: rendered }) => {
      if (active) setSvg(rendered)
    }).catch(() => setSvg(''))
    return () => { active = false }
  }, [])

  return svg ? <div className="mermaid-wrap" dangerouslySetInnerHTML={{ __html: svg }} /> : <div className="diagram-fallback">Architecture diagram unavailable</div>
}

function StatusBadge({ status }) {
  const success = status === 'success' || status === 'passed'
  const warning = status === 'circuit_breaker_timeout' || status === 'failed_after_max_iterations'
  return (
    <span className={`status-badge ${success ? 'status-success' : warning ? 'status-warning' : 'status-error'}`}>
      {success ? <CheckCircle2 size={13} /> : warning ? <AlertTriangle size={13} /> : <XCircle size={13} />}
      {status || 'idle'}
    </span>
  )
}

function Metric({ label, value, icon: Icon }) {
  return (
    <div className="metric-card">
      <div className="metric-label"><Icon size={14} /> {label}</div>
      <strong>{value}</strong>
    </div>
  )
}

function RolePermissionTooltip({ role }) {
  const policy = rolePermissions[role]
  if (!policy) return null

  const flag = (value) => (value ? 'Yes' : 'No')

  return (
    <span className="role-info">
      <button type="button" className="role-info-btn" aria-label={`Quyền của role ${role}`}>
        <Info size={13} />
      </button>
      <div className="role-tooltip" role="tooltip">
        <div className="role-tooltip-title">{role.toUpperCase()} POLICY</div>
        <div className="role-tooltip-row"><span>Catalogs</span><strong>{policy.catalogs.join(', ')}</strong></div>
        <div className="role-tooltip-row"><span>Export file</span><strong>{flag(policy.canExportFile)}</strong></div>
        <div className="role-tooltip-row"><span>Access PII</span><strong>{flag(policy.canAccessPii)}</strong></div>
        <div className="role-tooltip-row"><span>Execute DDL</span><strong>{flag(policy.canExecuteDdl)}</strong></div>
        <div className="role-tooltip-row"><span>Max rows</span><strong>{policy.maxRowLimit.toLocaleString()}</strong></div>
        <div className="role-tooltip-section">Allowed tables</div>
        <ul>{policy.allowed.map((table) => <li key={table}>{table}</li>)}</ul>
        <div className="role-tooltip-section">Denied tables</div>
        {policy.denied.length ? <ul>{policy.denied.map((table) => <li key={table}>{table}</li>)}</ul> : <p className="role-tooltip-empty">None</p>}
      </div>
    </span>
  )
}

function App() {
  const [role, setRole] = useState('analyst')
  const [scenarioId, setScenarioId] = useState(scenarios[0].id)
  const [query, setQuery] = useState(scenarios[0].prompt_text)
  const [activeTab, setActiveTab] = useState('monitor')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [executionSteps, setExecutionSteps] = useState([])
  const [xrayEvents, setXrayEvents] = useState([])
  const consoleRef = useRef(null)
  const abortControllerRef = useRef(null)

  const scenario = useMemo(() => scenarios.find((item) => item.id === scenarioId) || scenarios[0], [scenarioId])

  useEffect(() => {
    const consoleElement = consoleRef.current
    if (consoleElement) consoleElement.scrollTop = consoleElement.scrollHeight
  }, [executionSteps])

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  const selectScenario = (event) => {
    const next = scenarios.find((item) => item.id === event.target.value) || scenarios[0]
    setScenarioId(next.id)
    setQuery(next.prompt_text)
    setError('')
  }

  const cancelQuery = () => {
    abortControllerRef.current?.abort()
  }

  const executeQuery = async () => {
    if (!query.trim() || loading) return
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    setLoading(true)
    setError('')
    setResult(null)
    setExecutionSteps([])
    setXrayEvents([])
    setActiveTab('monitor')

    try {
      const response = await fetch(`${API_BASE_URL}/agent/query_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/x-ndjson' },
        signal: controller.signal,
        body: JSON.stringify({
          query: query.trim(),
          role,
          max_iterations: 3,
          timeout_seconds: 5,
        }),
      })

      if (!response.ok) {
        throw new Error(`Secure pipeline returned HTTP ${response.status}`)
      }
      if (!response.body) {
        throw new Error('Trình duyệt không hỗ trợ đọc response stream.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const handleLine = (line) => {
        if (!line.trim()) return
        let event
        try {
          event = JSON.parse(line)
        } catch {
          setExecutionSteps((steps) => [...steps, '⚠️ Nhận được dữ liệu stream không hợp lệ.'])
          return
        }

        if (event.type === 'step') {
          setExecutionSteps((steps) => [...steps, event.message || 'Đang xử lý...'])
          if (event.xray_data && typeof event.xray_data === 'object') {
            setXrayEvents((events) => [...events, event.xray_data])
          }
        } else if (event.type === 'final_result') {
          setResult(event.data)
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Secure pipeline thất bại.')
        }
      }

      while (true) {
        const { value, done } = await reader.read()
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        lines.forEach(handleLine)
        if (done) break
      }
      if (buffer.trim()) handleLine(buffer)
    } catch (requestError) {
      if (requestError?.name === 'AbortError') {
        setError('Đã hủy pipeline.')
        setExecutionSteps((steps) => [...steps, '⛔ Pipeline đã bị hủy.'])
      } else {
        const message = requestError instanceof Error ? requestError.message : 'Không thể kết nối tới Secure Agent API.'
        setError(message)
      }
      setResult(null)
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
      setLoading(false)
    }
  }

  const rawData = result?.raw_data
  const prettyRawData = typeof rawData === 'string' ? rawData : JSON.stringify(rawData ?? {}, null, 2)

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><ShieldCheck size={23} /></div>
          <div><div className="eyebrow">NEURO-SYMBOLIC / BI SECURITY</div><h1>Secure Agentic BI</h1></div>
        </div>
        <div className="topbar-status"><span className="pulse" /> DEFENSE CONSOLE <span className="topbar-divider" /> v1.0.0</div>
      </header>

      <section className="dashboard-grid">
        <aside className="left-pane">
          <div className="pane-heading"><div><div className="eyebrow">RED TEAMING / INTERACTION</div><h2>Defense Console</h2></div><LockKeyhole size={18} className="muted" /></div>

          <div className="control-grid">
            <label>
              <span className="label-with-info">ACTOR ROLE <RolePermissionTooltip role={role} /></span>
              <select value={role} onChange={(event) => setRole(event.target.value)}>{roles.map((item) => <option key={item}>{item}</option>)}</select>
            </label>
            <label>ATTACK SCENARIO<select value={scenarioId} onChange={selectScenario}>{scenarios.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></label>
          </div>

          <div className="intel-card">
            <div className="card-kicker"><AlertTriangle size={14} /> THREAT INTELLIGENCE</div>
            <div className="intel-title">{scenario.attack_group}</div>
            <p>{scenario.description}</p>
            <a href={scenario.paper_url} target="_blank" rel="noreferrer">{scenario.paper_reference} <ChevronRight size={13} /></a>
          </div>

          <label className="query-label">NATURAL LANGUAGE QUERY<textarea value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nhập câu hỏi BI hoặc chọn một kịch bản..." /></label>
          <div className="action-row">
            <button className="execute-button" onClick={executeQuery} disabled={loading || !query.trim()}>{loading ? <><RefreshCw size={17} className="spin" /> RUNNING PIPELINE...</> : <><Play size={17} /> EXECUTE SECURE QUERY</>}</button>
            {loading && <button type="button" className="cancel-button" onClick={cancelQuery}><XCircle size={17} /> CANCEL</button>}
          </div>

          {error && <div className="error-banner"><XCircle size={17} /><div><strong>{error === 'Đã hủy pipeline.' ? 'Cancelled' : 'Request failed'}</strong><span>{error}</span></div></div>}

          <div className="attempts-card">
            <div className="card-kicker"><RefreshCw size={14} /> REFLEXION HISTORY</div>
            {loading ? <div className="skeleton-stack"><span /><span /><span /></div> : result?.iteration_history?.length ? (
              <div className="history-list">
                {result.iteration_history.map((item) => (
                  <div className={`history-item ${item.status === 'success' ? 'history-success' : 'history-failure'}`} key={item.attempt_number}>
                    <div className="history-top"><span className="attempt">ATTEMPT {String(item.attempt_number).padStart(2, '0')}</span><StatusBadge status={item.status} /></div>
                    <div className="sql-block"><Code2 size={14} /><code>{item.generated_sql || 'No SQL generated'}</code></div>
                    {item.error_message && <div className="history-error"><AlertTriangle size={14} /> {item.error_message}</div>}
                  </div>
                ))}
              </div>
            ) : <div className="empty-state">Lịch sử attempt sẽ xuất hiện tại đây sau khi pipeline chạy.</div>}
          </div>
        </aside>

        <section className="right-pane">
          <div className="pane-heading monitor-heading"><div><div className="eyebrow">OBSERVABILITY / AUDIT TRAIL</div><h2>Pipeline Monitor</h2></div><div className="live-indicator"><span className="pulse" /> LIVE</div></div>
          <nav className="tabs">{tabs.map(({ id, label, icon: Icon }) => <button key={id} className={activeTab === id ? 'tab active' : 'tab'} onClick={() => setActiveTab(id)}><Icon size={15} /> {label}</button>)}</nav>

          {!result && !loading && activeTab === 'monitor' && <div className="welcome-panel"><div className="welcome-icon"><Terminal size={25} /></div><h3>Ready for secure execution</h3><p>Chọn một kịch bản red-team hoặc nhập truy vấn BI để quan sát đầy đủ 6 lớp phòng thủ.</p><div className="flow-hint"><span>RBAC</span><ChevronRight size={13} /><span>LLM</span><ChevronRight size={13} /><span>AST</span><ChevronRight size={13} /><span>REFLEXION</span><ChevronRight size={13} /><span>TAINT</span></div></div>}
          {loading && <ThinkingConsole steps={executionSteps} consoleRef={consoleRef} />}

          {activeTab === 'monitor' && result && !loading && <Monitor result={result} />}
          {activeTab === 'xray' && <ExecutionTrace events={xrayEvents} loading={loading} />}
          {activeTab === 'raw' && <pre className="raw-panel">{prettyRawData}</pre>}
          {activeTab === 'theory' && <Theory />}
          {activeTab === 'comparison' && <Comparison />}
        </section>
      </section>
    </main>
  )
}

function TraceValue({ label, value, code = false, json = false }) {
  if (value === undefined || value === null || value === '') return null
  const serialized = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  return (
    <div className="trace-field">
      <div className="trace-label">{label}</div>
      {json && typeof value === 'object' ? <pre className="trace-json">{serialized}</pre> : code ? <pre className="trace-code">{serialized}</pre> : <pre className="trace-text">{serialized}</pre>}
    </div>
  )
}

function ExecutionTrace({ events, loading }) {
  return (
    <div className="execution-trace">
      <div className="trace-summary">
        <div><div className="eyebrow">X-RAY / STRUCTURED EVENTS</div><h2>Execution Trace</h2></div>
        <span className="count-chip">{events.length} EVENTS</span>
      </div>
      {!events.length && <div className="empty-state">{loading ? 'Đang chờ bước hoàn tất để ghi nhận X-Ray...' : 'Chạy pipeline để xem trace chi tiết.'}</div>}
      <div className="trace-list">
        {events.map((event, index) => {
          const failed = Boolean(event.error)
          return (
            <details className={`trace-card ${failed ? 'trace-failed' : ''}`} open key={`${event.step}-${event.attempt_number || 'single'}-${index}`}>
              <summary>
                <span className="trace-index">{String(index + 1).padStart(2, '0')}</span>
                <span>{event.step}{event.attempt_number ? ` / Attempt ${event.attempt_number}` : ''}</span>
                <span className={`trace-state ${failed ? 'trace-state-error' : 'trace-state-ok'}`}>{failed ? 'ERROR' : 'CAPTURED'}</span>
              </summary>
              <div className="trace-content">
                <TraceValue label="Target" value={event.target} />
                <TraceValue label="Execution Detail / Prompt" value={event.execution_detail} />
                <TraceValue label="Input" value={event.input} code={typeof event.input === 'string' && /select|from|where/i.test(event.input)} json={typeof event.input === 'object'} />
                {event.output !== undefined && <TraceValue label="Output" value={event.output} json={typeof event.output === 'object'} code={typeof event.output === 'string' && /select|from|where/i.test(event.output)} />}
                {event.error && <TraceValue label="Error" value={event.error} />}
              </div>
            </details>
          )
        })}
      </div>
    </div>
  )
}

function ThinkingConsole({ steps, consoleRef }) {
  return <div className="thinking-console">
    <div className="console-header"><span className="console-dot console-red" /><span className="console-dot console-yellow" /><span className="console-dot console-green" /><span className="console-title"><Terminal size={13} /> SECURE PIPELINE / LIVE TRACE</span></div>
    <div className="console-body" ref={consoleRef} role="log" aria-live="polite">
      {steps.length === 0 && <div className="console-line console-muted">▌ Khởi tạo secure pipeline...</div>}
      {steps.map((step, index) => <div className="console-line" key={`${step}-${index}`}><span className="console-index">{String(index + 1).padStart(2, '0')}</span><span>{step}</span></div>)}
      <div className="console-cursor">▌</div>
    </div>
  </div>
}

function Monitor({ result }) {
  return <div className="monitor-content">
    <div className="metrics-grid">
      <Metric label="STATUS" value={<StatusBadge status={result.status} />} icon={ShieldCheck} />
      <Metric label="ITERATIONS" value={result.total_iterations_used ?? 0} icon={RefreshCw} />
      <Metric label="DB EXECUTION" value={`${Number(result.execution_time_seconds || 0).toFixed(3)}s`} icon={Clock3} />
    </div>
    {result.status === 'circuit_breaker_timeout' && <div className="error-banner"><Clock3 size={17} /><div><strong>Circuit breaker opened</strong><span>Trino query exceeded the configured execution budget.</span></div></div>}
    <div className="answer-card">
      <div className="card-kicker"><Bot size={14} /> FINAL ANSWER / TAINT FILTERED</div>
      {result?.final_answer ? <div className="markdown-body"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result.final_answer}</ReactMarkdown></div> : <div className="empty-state">Không có câu trả lời an toàn từ pipeline.</div>}
    </div>
  </div>
}

function Theory() {
  const steps = [
    ['01', 'Authentication & Context', 'RBAC resolves the actor policy and injects only an allow-listed schema context.'],
    ['02', 'Metadata Discovery', 'Trino metadata is grouped by table and denied objects are removed before reaching the model.'],
    ['03', 'ReAct Neural Phase', 'Gemini reasons over the constrained context and emits a read-only SQL plan.'],
    ['04', 'AST Guardrail', 'sqlglot blocks DML/DDL, recursive CTEs, unsafe joins, and out-of-scope tables.'],
    ['05', 'Reflexion Loop', 'AST or database errors become feedback so the agent can repair SQL within a fixed budget.'],
    ['06', 'Taint Filter', 'Database rows remain passive text; suspicious instructions are reported, never executed.'],
  ]
  return <div className="theory-panel"><MermaidDiagram /><div className="section-title"><span>DEFENSE LAYERS</span><span className="count-chip">6 STEPS</span></div><div className="theory-grid">{steps.map(([number, title, body]) => <article key={number}><span className="step-number">{number}</span><div><h3>{title}</h3><p>{body}</p></div></article>)}</div></div>
}

function Comparison() {
  return <div className="comparison-panel"><div className="section-title"><span>API EVOLUTION</span><span className="count-chip">SECURITY POSTURE</span></div><div className="comparison-table"><div className="comparison-row comparison-head"><span>ENDPOINT</span><span>CONTROLS</span><span>BEHAVIOR</span></div>{[
    ['/query', 'AST Guardrail', 'Blocks unsafe SQL; no repair loop'],
    ['/query_reflexion', 'AST + Reflexion', 'Repairs AST and Trino errors'],
    ['/query_secure_pipeline', 'AST + Reflexion + Circuit Breaker + Taint Filter', 'Complete secure execution pipeline'],
  ].map(([endpoint, controls, behavior]) => <div className="comparison-row" key={endpoint}><code>{endpoint}</code><span>{controls}</span><span>{behavior}</span></div>)}</div></div>
}

export default App
