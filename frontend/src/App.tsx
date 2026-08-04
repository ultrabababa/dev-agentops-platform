import { useCallback, useEffect, useState } from "react";

type HealthResponse = {
  status: string;
};

type VersionResponse = {
  version: string;
};

type StorageStatus = {
  path: string;
  exists: boolean;
  initialized: boolean;
  schema_version: string | null;
  table_count: number;
  tables: string[];
};

type DashboardStatus = {
  health: HealthResponse;
  version: VersionResponse;
  storage: StorageStatus;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function StatusDot({ active }: { active: boolean }) {
  return <span className={active ? "status-dot active" : "status-dot"} />;
}

function App() {
  const [status, setStatus] = useState<DashboardStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [health, version, storage] = await Promise.all([
        fetchJson<HealthResponse>("/health"),
        fetchJson<VersionResponse>("/version"),
        fetchJson<StorageStatus>("/storage/status"),
      ]);
      setStatus({ health, version, storage });
      setLastUpdated(new Date());
    } catch (requestError) {
      const message =
        requestError instanceof Error ? requestError.message : "未知错误";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  const apiHealthy = status?.health.status === "ok";

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#main" aria-label="DevAgentOps 首页">
          <span className="brand-mark">DA</span>
          <span>
            <strong>DevAgentOps</strong>
            <small>Evaluation Foundation</small>
          </span>
        </a>
        <div className="environment-pill">
          <StatusDot active={apiHealthy} />
          Local V1
        </div>
      </header>

      <main id="main">
        <section className="hero">
          <div>
            <p className="eyebrow">Issue #3 · Application smoke path</p>
            <h1>本地评测基础设施状态</h1>
            <p className="hero-copy">
              从 CLI、SQLite 到 FastAPI 与 React 的最小只读链路。当前页面只展示真实系统状态，不触发 Agent、评测或数据写入。
            </p>
          </div>
          <div className="refresh-cluster">
            <button type="button" onClick={() => void loadStatus()} disabled={loading}>
              {loading ? "正在读取…" : "刷新状态"}
            </button>
            <small aria-live="polite">
              {lastUpdated
                ? `更新于 ${lastUpdated.toLocaleTimeString("zh-CN", {
                    hour12: false,
                  })}`
                : "等待首次读取"}
            </small>
          </div>
        </section>

        {error ? (
          <section className="error-panel" role="alert">
            <p className="eyebrow">Backend unavailable</p>
            <h2>无法读取后端状态</h2>
            <p>
              请确认 FastAPI 已在 <code>127.0.0.1:8000</code> 启动。请求结果：
              <code>{error}</code>
            </p>
            <button type="button" onClick={() => void loadStatus()}>
              重新连接
            </button>
          </section>
        ) : null}

        {!error && loading && !status ? (
          <section className="status-grid" aria-label="正在读取后端状态">
            <div className="status-card skeleton-card" />
            <div className="status-card skeleton-card" />
            <div className="status-card storage-card skeleton-card" />
          </section>
        ) : null}

        {!error && status ? (
          <section className="status-grid" aria-label="后端状态">
            <article className="status-card">
              <div className="card-heading">
                <span className="card-index">01</span>
                <span className={apiHealthy ? "state-tag good" : "state-tag bad"}>
                  {apiHealthy ? "API 在线" : "API 异常"}
                </span>
              </div>
              <div>
                <p className="card-label">FastAPI health</p>
                <h2>{status.health.status}</h2>
              </div>
              <p className="card-note">HTTP 服务能够接收并响应请求。</p>
            </article>

            <article className="status-card">
              <div className="card-heading">
                <span className="card-index">02</span>
                <span className="state-tag neutral">Build identity</span>
              </div>
              <div>
                <p className="card-label">Application version</p>
                <h2>v{status.version.version}</h2>
              </div>
              <p className="card-note">由 Python 包版本提供，而不是前端写死。</p>
            </article>

            <article className="status-card storage-card">
              <div className="card-heading">
                <span className="card-index">03</span>
                <span
                  className={
                    status.storage.initialized ? "state-tag good" : "state-tag neutral"
                  }
                >
                  {status.storage.initialized ? "已初始化" : "尚未初始化"}
                </span>
              </div>

              <div className="storage-summary">
                <div>
                  <p className="card-label">SQLite storage</p>
                  <h2>{status.storage.exists ? "Ready" : "Not created"}</h2>
                </div>
                <dl>
                  <div>
                    <dt>Schema</dt>
                    <dd>{status.storage.schema_version ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>Tables</dt>
                    <dd>{status.storage.table_count}</dd>
                  </div>
                </dl>
              </div>

              <div className="path-row">
                <span>Resolved path</span>
                <code>{status.storage.path}</code>
              </div>

              <div className="table-list" aria-label="SQLite 数据表">
                {status.storage.tables.length > 0 ? (
                  status.storage.tables.map((table) => <code key={table}>{table}</code>)
                ) : (
                  <span>当前数据库没有可展示的表。</span>
                )}
              </div>
            </article>
          </section>
        ) : null}

        <section className="boundary-strip" aria-label="V1 边界">
          <div>
            <p className="eyebrow">Current boundary</p>
            <h2>只读观察，不执行任务</h2>
          </div>
          <ul>
            <li>无模型 API</li>
            <li>无外部服务</li>
            <li>不修改数据库</li>
          </ul>
        </section>
      </main>

      <footer>
        <span>CLI</span>
        <i>→</i>
        <span>SQLite</span>
        <i>→</i>
        <span>FastAPI</span>
        <i>→</i>
        <span>React</span>
      </footer>
    </div>
  );
}

export default App;
