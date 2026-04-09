import { useState } from 'react'

function formatDollars(amount) {
  if (!amount) return '$0'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

export default function SearchPanel({ open, searching, ingesting, results, onIngest, onClose }) {
  const [selected, setSelected] = useState(new Set())

  const items = results?.results || []
  const hasError = results?.error

  const toggleSelect = (internalId) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(internalId)) {
        next.delete(internalId)
      } else {
        next.add(internalId)
      }
      return next
    })
  }

  const toggleAll = () => {
    if (selected.size === items.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(items.map((r) => r.internal_id).filter(Boolean)))
    }
  }

  const handleIngest = () => {
    const ids = Array.from(selected)
    if (ids.length === 0) return
    onIngest(ids)
    setSelected(new Set())
  }

  return (
    <div
      className={`absolute top-0 right-0 h-full w-[420px] bg-gray-900 border-l border-gray-700 shadow-2xl transition-transform duration-300 ease-in-out z-40 flex flex-col ${
        open ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div>
          <div className="text-sm font-medium text-white">Search Results</div>
          {results && !hasError && (
            <div className="text-xs text-gray-400 mt-0.5">
              {results.result_count} of {results.total_available?.toLocaleString()} total
            </div>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white transition-colors p-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Searching state */}
        {searching && (
          <div className="flex items-center justify-center h-32 text-gray-500">
            <div className="flex items-center gap-2 text-xs">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Querying USASpending.gov...
            </div>
          </div>
        )}

        {/* Error state */}
        {hasError && !searching && (
          <div className="p-4 text-xs text-red-400">
            {results.error}
          </div>
        )}

        {/* Results list */}
        {!searching && !hasError && items.length > 0 && (
          <div>
            {items.map((r) => (
              <div
                key={r.internal_id || r.award_id}
                onClick={() => r.internal_id && toggleSelect(r.internal_id)}
                className={`px-4 py-3 border-b border-gray-800 cursor-pointer transition-colors ${
                  selected.has(r.internal_id)
                    ? 'bg-cyan-900/30 border-l-2 border-l-cyan-400'
                    : 'hover:bg-gray-800/50 border-l-2 border-l-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-white truncate">
                      {r.recipient_name || 'Unknown Recipient'}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5 font-mono">
                      {r.award_id || 'No PIID'}
                    </div>
                  </div>
                  <div className="text-xs font-medium text-cyan-400 shrink-0">
                    {formatDollars(r.award_amount)}
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
                  <span>{r.awarding_sub_agency || r.awarding_agency || ''}</span>
                  {r.start_date && <span>{r.start_date}</span>}
                </div>
                {r.award_type && (
                  <div className="mt-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
                      {r.award_type}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!searching && !hasError && results && items.length === 0 && (
          <div className="flex items-center justify-center h-32 text-gray-500 text-xs">
            No awards found
          </div>
        )}
      </div>

      {/* Footer — selection actions */}
      {items.length > 0 && (
        <div className="border-t border-gray-700 px-4 py-3 bg-gray-900">
          <div className="flex items-center justify-between">
            <button
              onClick={toggleAll}
              className="text-xs text-gray-400 hover:text-white transition-colors"
            >
              {selected.size === items.length ? 'Deselect all' : 'Select all'}
            </button>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500">
                {selected.size} selected
              </span>
              <button
                onClick={handleIngest}
                disabled={selected.size === 0 || ingesting}
                className="px-4 py-1.5 text-xs rounded bg-cyan-700 hover:bg-cyan-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
              >
                {ingesting ? 'Ingesting...' : 'Ingest to Graph'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}