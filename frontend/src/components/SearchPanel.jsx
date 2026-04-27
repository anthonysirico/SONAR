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

// ─── Source Status Badge ────────────────────────────────────

function SourceStatus({ status, error, reason }) {
  if (status === 'success') {
    return (
      <span className="flex items-center gap-1 text-xs text-emerald-400">
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </span>
    )
  }
  if (status === 'skipped') {
    return (
      <span className="text-xs text-gray-500" title={reason || 'Skipped'}>
        skipped
      </span>
    )
  }
  if (status === 'error') {
    return (
      <span className="text-xs text-red-400" title={error || 'Error'}>
        error
      </span>
    )
  }
  return null
}

// ─── USASpending Result Card ────────────────────────────────

function USASpendingCard({ r, selected, onToggle }) {
  return (
    <div
      onClick={() => r.internal_id && onToggle(r.internal_id)}
      className={`px-4 py-3 border-b border-gray-800 cursor-pointer transition-colors ${
        selected
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
  )
}

// ─── SAM.gov Result Card ────────────────────────────────────

function SAMGovCard({ r, selected, onToggle }) {
  return (
    <div
      onClick={() => r.uei && onToggle(r.uei)}
      className={`px-4 py-3 border-b border-gray-800 cursor-pointer transition-colors ${
        selected
          ? 'bg-purple-900/30 border-l-2 border-l-purple-400'
          : 'hover:bg-gray-800/50 border-l-2 border-l-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-white truncate">
            {r.legal_business_name || 'Unknown Entity'}
          </div>
          {r.dba_name && (
            <div className="text-xs text-gray-500 mt-0.5 italic">
              DBA: {r.dba_name}
            </div>
          )}
          <div className="text-xs text-gray-500 mt-0.5 font-mono">
            UEI: {r.uei || 'N/A'}
            {r.cage_code && r.cage_code !== 'null' && (
              <span className="ml-2">CAGE: {r.cage_code}</span>
            )}
          </div>
        </div>
        <div className="shrink-0 flex flex-col items-end gap-1">
          <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
            r.registration_status === 'Active'
              ? 'bg-emerald-500/10 text-emerald-400'
              : 'bg-amber-500/10 text-amber-400'
          }`}>
            {r.registration_status || 'Unknown'}
          </span>
          {r.exclusion_flag && (
            <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/10 text-red-400 font-medium">
              EXCLUDED
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
        {r.entity_type && <span>{r.entity_type}</span>}
        {r.address && <span className="truncate">{r.address}</span>}
      </div>
      {r.state_of_incorporation && (
        <div className="mt-1">
          <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
            Inc: {r.state_of_incorporation}
          </span>
        </div>
      )}
    </div>
  )
}

// ─── ProPublica 990 Result Card ───────────────────────────

function ProPublica990Card({ r, selected, onToggle }) {
  return (
    <div
      onClick={() => r.ein && onToggle(r.ein)}
      className={`px-4 py-3 border-b border-gray-800 cursor-pointer transition-colors ${
        selected
          ? 'bg-emerald-900/30 border-l-2 border-l-emerald-400'
          : 'hover:bg-gray-800/50 border-l-2 border-l-transparent'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-white truncate">
            {r.name || 'Unknown Organization'}
          </div>
          {r.sub_name && (
            <div className="text-xs text-gray-500 mt-0.5 italic">
              {r.sub_name}
            </div>
          )}
          <div className="text-xs text-gray-500 mt-0.5 font-mono">
            EIN: {r.strein || r.ein || 'N/A'}
          </div>
        </div>
        <div className="shrink-0 text-right">
          {r.revenue_amount > 0 && (
            <div className="text-xs font-medium text-emerald-400">
              {formatDollars(r.revenue_amount)}
            </div>
          )}
          {r.income_amount > 0 && r.income_amount !== r.revenue_amount && (
            <div className="text-xs text-gray-500">
              Income: {formatDollars(r.income_amount)}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
        {r.city && <span>{r.city}, {r.state}</span>}
        {r.ntee_code && (
          <span className="px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
            NTEE: {r.ntee_code}
          </span>
        )}
      </div>
      {r.asset_amount > 0 && (
        <div className="mt-1 text-xs text-gray-500">
          Assets: {formatDollars(r.asset_amount)}
        </div>
      )}
    </div>
  )
}

// ─── OpenCorporates Result Card ───────────────────────────

function OpenCorpCard({ r }) {
  return (
    <div className="px-4 py-3 border-b border-gray-800 border-l-2 border-l-transparent hover:bg-gray-800/50 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-white truncate">
            {r.name || 'Unknown Company'}
          </div>
          <div className="text-xs text-gray-500 mt-0.5 font-mono">
            {r.jurisdiction_code?.toUpperCase()} — #{r.company_number || 'N/A'}
          </div>
        </div>
        <span className={`text-xs px-1.5 py-0.5 rounded font-medium shrink-0 ${
          r.current_status === 'Active'
            ? 'bg-emerald-500/10 text-emerald-400'
            : r.current_status === 'Dissolved'
              ? 'bg-red-500/10 text-red-400'
              : 'bg-gray-800 text-gray-400'
        }`}>
          {r.current_status || 'Unknown'}
        </span>
      </div>

      <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-500">
        {r.company_type && <span>{r.company_type}</span>}
        {r.incorporation_date && <span>Inc: {r.incorporation_date}</span>}
      </div>
      {r.registered_address && (
        <div className="mt-1 text-xs text-gray-500 truncate">
          {r.registered_address}
        </div>
      )}
    </div>
  )
}


// ─── Main SearchPanel ───────────────────────────────────────

export default function SearchPanel({
  open,
  searching,
  ingesting,
  enriching,
  results,
  onIngest,
  onEnrich,
  onEnrichNonprofit,
  onClose,
}) {
  const [selectedUSA, setSelectedUSA] = useState(new Set())
  const [selectedSAM, setSelectedSAM] = useState(new Set())
  const [selected990, setSelected990] = useState(new Set())
  const [expandedSources, setExpandedSources] = useState({})

  // Multi-source results structure: results.sources = { usaspending: {...}, sam_gov: {...} }
  const sources = results?.sources || {}

  const toggleUSA = (id) => {
    setSelectedUSA((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleSAM = (uei) => {
    setSelectedSAM((prev) => {
      const next = new Set(prev)
      next.has(uei) ? next.delete(uei) : next.add(uei)
      return next
    })
  }

  const toggle990 = (ein) => {
    setSelected990((prev) => {
      const next = new Set(prev)
      next.has(ein) ? next.delete(ein) : next.add(ein)
      return next
    })
  }

  const toggleSource = (sid) => {
    setExpandedSources((prev) => ({
      ...prev,
      [sid]: !prev[sid],
    }))
  }

  const handleIngest = () => {
    const ids = Array.from(selectedUSA)
    if (ids.length === 0) return
    onIngest(ids)
    setSelectedUSA(new Set())
  }

  const handleEnrich = () => {
    const ueis = Array.from(selectedSAM)
    if (ueis.length === 0) return
    onEnrich(ueis)
    setSelectedSAM(new Set())
  }

  const handleEnrich990 = () => {
    const eins = Array.from(selected990)
    if (eins.length === 0) return
    onEnrichNonprofit?.(eins)
    setSelected990(new Set())
  }

  const usaData = sources.usaspending || {}
  const samData = sources.sam_gov || {}
  const ppData = sources.propublica_990 || {}
  const ocData = sources.open_corporates || {}
  const usaItems = usaData.results || []
  const samItems = samData.results || []
  const ppItems = ppData.results || []
  const ocItems = ocData.results || []

  const hasAnyResults = usaItems.length > 0 || samItems.length > 0 || ppItems.length > 0 || ocItems.length > 0
  const hasAnyError = usaData.status === 'error' || samData.status === 'error'

  // Default to expanded
  const isUSAExpanded = expandedSources.usaspending !== false
  const isSAMExpanded = expandedSources.sam_gov !== false
  const isPPExpanded = expandedSources.propublica_990 !== false
  const isOCExpanded = expandedSources.open_corporates !== false

  return (
    <div
      className={`absolute top-0 right-0 h-full w-[440px] bg-gray-900 border-l border-gray-700 shadow-2xl transition-transform duration-300 ease-in-out z-40 flex flex-col ${
        open ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div>
          <div className="text-sm font-medium text-white">Search Results</div>
          {results && !searching && (
            <div className="text-xs text-gray-400 mt-0.5">
              {Object.values(sources).filter(s => s.status === 'success').length} source(s) queried
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
              Querying data sources...
            </div>
          </div>
        )}

        {/* Results by source */}
        {!searching && results && (
          <>
            {/* ── USASpending Section ── */}
            {usaData.source_name && (
              <div>
                <button
                  onClick={() => toggleSource('usaspending')}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-800/50 border-b border-gray-700 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <svg className={`w-3 h-3 text-gray-400 transition-transform ${isUSAExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-xs font-medium text-cyan-400">
                      {usaData.source_name}
                    </span>
                    {usaData.status === 'success' && (
                      <span className="text-xs text-gray-500">
                        {usaData.result_count} of {usaData.total_available?.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <SourceStatus status={usaData.status} error={usaData.error} reason={usaData.reason} />
                </button>

                {isUSAExpanded && usaItems.length > 0 && (
                  <div>
                    {usaItems.map((r) => (
                      <USASpendingCard
                        key={r.internal_id || r.award_id}
                        r={r}
                        selected={selectedUSA.has(r.internal_id)}
                        onToggle={toggleUSA}
                      />
                    ))}
                  </div>
                )}

                {isUSAExpanded && usaData.status === 'error' && (
                  <div className="px-4 py-3 text-xs text-red-400">
                    {usaData.error}
                  </div>
                )}

                {isUSAExpanded && usaData.status === 'success' && usaItems.length === 0 && (
                  <div className="px-4 py-3 text-xs text-gray-500">
                    No awards found
                  </div>
                )}
              </div>
            )}

            {/* ── SAM.gov Section ── */}
            {samData.source_name && (
              <div>
                <button
                  onClick={() => toggleSource('sam_gov')}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-800/50 border-b border-gray-700 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <svg className={`w-3 h-3 text-gray-400 transition-transform ${isSAMExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-xs font-medium text-purple-400">
                      {samData.source_name}
                    </span>
                    {samData.status === 'success' && (
                      <span className="text-xs text-gray-500">
                        {samData.result_count} result(s)
                      </span>
                    )}
                  </div>
                  <SourceStatus status={samData.status} error={samData.error} reason={samData.reason} />
                </button>

                {isSAMExpanded && samItems.length > 0 && (
                  <div>
                    {samItems.map((r) => (
                      <SAMGovCard
                        key={r.uei || r.legal_business_name}
                        r={r}
                        selected={selectedSAM.has(r.uei)}
                        onToggle={toggleSAM}
                      />
                    ))}
                  </div>
                )}

                {isSAMExpanded && samData.status === 'skipped' && (
                  <div className="px-4 py-3 text-xs text-gray-500 italic">
                    {samData.reason || 'No credentials provided — click the SAM badge in the toolbar to connect'}
                  </div>
                )}

                {isSAMExpanded && samData.status === 'error' && (
                  <div className="px-4 py-3 text-xs text-red-400">
                    {samData.error}
                  </div>
                )}

                {isSAMExpanded && samData.status === 'success' && samItems.length === 0 && (
                  <div className="px-4 py-3 text-xs text-gray-500">
                    No entities found
                  </div>
                )}
              </div>
            )}

            {/* ── ProPublica 990 Section ── */}
            {ppData.source_name && (
              <div>
                <button
                  onClick={() => toggleSource('propublica_990')}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-800/50 border-b border-gray-700 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <svg className={`w-3 h-3 text-gray-400 transition-transform ${isPPExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-xs font-medium text-emerald-400">
                      {ppData.source_name}
                    </span>
                    {ppData.status === 'success' && (
                      <span className="text-xs text-gray-500">
                        {ppData.result_count} of {ppData.total_available?.toLocaleString()}
                      </span>
                    )}
                  </div>
                  <SourceStatus status={ppData.status} error={ppData.error} reason={ppData.reason} />
                </button>

                {isPPExpanded && ppItems.length > 0 && (
                  <div>
                    {ppItems.map((r) => (
                      <ProPublica990Card
                        key={r.ein || r.name}
                        r={r}
                        selected={selected990.has(r.ein)}
                        onToggle={toggle990}
                      />
                    ))}
                  </div>
                )}

                {isPPExpanded && ppData.status === 'success' && ppItems.length === 0 && (
                  <div className="px-4 py-3 text-xs text-gray-500">
                    No nonprofit filings found
                  </div>
                )}
              </div>
            )}

            {/* ── OpenCorporates Section ── */}
            {ocData.source_name && (
              <div>
                <button
                  onClick={() => toggleSource('open_corporates')}
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-800/50 border-b border-gray-700 hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <svg className={`w-3 h-3 text-gray-400 transition-transform ${isOCExpanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <span className="text-xs font-medium text-amber-400">
                      {ocData.source_name}
                    </span>
                    {ocData.status === 'success' && (
                      <span className="text-xs text-gray-500">
                        {ocData.result_count} result(s)
                      </span>
                    )}
                  </div>
                  <SourceStatus status={ocData.status} error={ocData.error} reason={ocData.reason} />
                </button>

                {isOCExpanded && ocItems.length > 0 && (
                  <div>
                    {ocItems.map((r) => (
                      <OpenCorpCard
                        key={`${r.jurisdiction_code}-${r.company_number}`}
                        r={r}
                      />
                    ))}
                  </div>
                )}

                {isOCExpanded && ocData.status === 'skipped' && (
                  <div className="px-4 py-3 text-xs text-gray-500 italic">
                    {ocData.reason || 'No credentials provided — click the OpenCorp badge to connect'}
                  </div>
                )}

                {isOCExpanded && ocData.status === 'error' && (
                  <div className="px-4 py-3 text-xs text-red-400">
                    {ocData.error}
                  </div>
                )}

                {isOCExpanded && ocData.status === 'success' && ocItems.length === 0 && (
                  <div className="px-4 py-3 text-xs text-gray-500">
                    No corporate registrations found
                  </div>
                )}
              </div>
            )}

            {/* No sources at all state */}
            {Object.keys(sources).length === 0 && (
              <div className="flex items-center justify-center h-32 text-gray-500 text-xs">
                No sources queried
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer — selection actions */}
      {(usaItems.length > 0 || samItems.length > 0 || ppItems.length > 0) && (
        <div className="border-t border-gray-700 px-4 py-3 bg-gray-900 space-y-2">
          {/* USASpending ingest action */}
          {usaItems.length > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                {selectedUSA.size} award(s) selected
              </span>
              <button
                onClick={handleIngest}
                disabled={selectedUSA.size === 0 || ingesting}
                className="px-4 py-1.5 text-xs rounded bg-cyan-700 hover:bg-cyan-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
              >
                {ingesting ? 'Ingesting...' : 'Ingest to Graph'}
              </button>
            </div>
          )}

          {/* SAM.gov enrich action */}
          {samItems.length > 0 && samData.status === 'success' && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                {selectedSAM.size} entity(s) selected
              </span>
              <button
                onClick={handleEnrich}
                disabled={selectedSAM.size === 0 || enriching}
                className="px-4 py-1.5 text-xs rounded bg-purple-700 hover:bg-purple-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
              >
                {enriching ? 'Enriching...' : 'Enrich Company'}
              </button>
            </div>
          )}

          {/* ProPublica 990 enrich action */}
          {ppItems.length > 0 && ppData.status === 'success' && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">
                {selected990.size} nonprofit(s) selected
              </span>
              <button
                onClick={handleEnrich990}
                disabled={selected990.size === 0 || enriching}
                className="px-4 py-1.5 text-xs rounded bg-emerald-700 hover:bg-emerald-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
              >
                {enriching ? 'Enriching...' : 'Enrich with 990'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}