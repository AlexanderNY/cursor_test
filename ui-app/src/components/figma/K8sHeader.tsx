export function K8sHeader() {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-[var(--border-color)] bg-[var(--bg-secondary)] px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-[var(--text-primary)]">
          Kubernetes Cluster Management
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="rounded-xl border border-[var(--border-color)] bg-[var(--bg-tertiary)] px-4 py-2 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--bg-tertiary)]/80 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
        >
          Add cluster
        </button>
        <div className="h-6 w-px bg-[var(--border-color)]" aria-hidden />
        <button
          type="button"
          className="rounded-xl p-2 text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-primary-500/50"
          aria-label="Refresh"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
    </header>
  )
}
