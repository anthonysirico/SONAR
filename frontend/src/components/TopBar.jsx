import { useState, useRef, useEffect } from 'react'

export default function TopBar({
  cases,
  activeCase,
  onSelectCase,
  onViewAll,
  onCreateCase,
  onDeleteCase,
  onSearch,
  onCompute,
  sources,
  sourceCredentials,
  onSourceClick,
}) {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState('keyword')
  const [caseDropdownOpen, setCaseDropdownOpen] = useState(false)
  const [createMode, setCreateMode] = useState(false)
  const [newCaseName, setNewCaseName] = useState('')
  const [newCaseDesc, setNewCaseDesc] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)

  const dropdownRef = useRef(null)
  const searchRef = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setCaseDropdownOpen(false)
        setCreateMode(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    if (!searchQuery.trim() || !activeCase) return
    onSearch(searchQuery.trim(), searchType)
  }

  const handleCreateCase = (e) => {
    e.preventDefault()
    if (!newCaseName.trim()) return
    onCreateCase(newCaseName.trim(), newCaseDesc.trim())
    setNewCaseName('')
    setNewCaseDesc('')
    setCreateMode(false)
    setCaseDropdownOpen(false)
  }

  // Count connected sources (those that don't need auth or have credentials)
  const activeSources = (sources || []).filter((s) => {
    if (!s.auth_required) return true
    return sourceCredentials && sourceCredentials[s.id]
  })
  const totalSources = (sources || []).length

  // Which sources participate in the current search type
  const applicableSources = (sources || []).filter((s) =>
    s.search_types?.includes(searchType)
  )

  return (
    <div className="flex items-center gap-4 px-4 py-2.5 bg-gray-900 border-b border-gray-700">

      {/* ── Brand ── */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-cyan-400 font-bold text-lg tracking-widest">SONAR</span>
      </div>

      {/* ── Case Selector ── */}
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setCaseDropdownOpen(!caseDropdownOpen)}
          className="flex items-center gap-2 px-3 py-1.5 text-xs rounded bg-gray-800 hover:bg-gray-700 border border-gray-600 transition-colors min-w-45"
        >
          <svg className="w-3.5 h-3.5 text-cyan-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <span className="truncate">
            {activeCase ? activeCase.name : 'Select Case'}
          </span>
          <svg className="w-3 h-3 text-gray-400 shrink-0 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {caseDropdownOpen && (
          <div className="absolute top-full left-0 mt-1 w-72 bg-gray-800 border border-gray-600 rounded shadow-xl z-50">
            {!createMode ? (
              <>
                {/* Existing cases */}
                <div className="max-h-48 overflow-y-auto">
                  {cases.length === 0 && (
                    <div className="px-3 py-2 text-xs text-gray-500">No cases yet</div>
                  )}
                  {cases.map((c) => (
                    <div
                      key={c.case_id}
                      className={`group flex items-center text-xs hover:bg-gray-700 transition-colors ${
                        activeCase?.case_id === c.case_id ? 'bg-gray-700 text-cyan-400' : 'text-gray-300'
                      }`}
                    >
                      <button
                        onClick={() => { onSelectCase(c); setCaseDropdownOpen(false) }}
                        className="flex-1 text-left px-3 py-2 flex items-center justify-between min-w-0"
                      >
                        <span className="truncate">{c.name}</span>
                        <span className="text-gray-500 shrink-0 ml-2">
                          {c.node_count ?? 0} nodes
                        </span>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (confirmDelete === c.case_id) {
                            onDeleteCase(c.case_id)
                            setConfirmDelete(null)
                            setCaseDropdownOpen(false)
                          } else {
                            setConfirmDelete(c.case_id)
                            setTimeout(() => setConfirmDelete(null), 2500)
                          }
                        }}
                        title={confirmDelete === c.case_id ? 'Click again to confirm' : 'Delete case'}
                        className={`shrink-0 px-2 py-2 transition-colors opacity-0 group-hover:opacity-100 ${
                          confirmDelete === c.case_id
                            ? 'text-red-400 opacity-100'
                            : 'text-gray-500 hover:text-red-400'
                        }`}
                      >
                        {confirmDelete === c.case_id ? (
                          <span className="text-xs font-medium">del?</span>
                        ) : (
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    </div>
                  ))}
                </div>

                <div className="border-t border-gray-600">
                  {activeCase && (
                    <button
                      onClick={() => { onViewAll(); setCaseDropdownOpen(false) }}
                      className="w-full text-left px-3 py-2 text-xs text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
                    >
                      View full graph
                    </button>
                  )}
                  <button
                    onClick={() => setCreateMode(true)}
                    className="w-full text-left px-3 py-2 text-xs text-cyan-400 hover:bg-gray-700 transition-colors flex items-center gap-1.5"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    New Case
                  </button>
                </div>
              </>
            ) : (
              /* ── Create case form ── */
              <div className="p-3">
                <div className="text-xs text-gray-400 mb-2 font-medium">New Investigation</div>
                <input
                  autoFocus
                  value={newCaseName}
                  onChange={(e) => setNewCaseName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateCase(e)}
                  placeholder="Case name"
                  className="w-full px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 mb-2"
                />
                <input
                  value={newCaseDesc}
                  onChange={(e) => setNewCaseDesc(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateCase(e)}
                  placeholder="Description (optional)"
                  className="w-full px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 mb-2"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleCreateCase}
                    className="flex-1 px-2 py-1.5 text-xs rounded bg-cyan-700 hover:bg-cyan-600 text-white transition-colors"
                  >
                    Create
                  </button>
                  <button
                    onClick={() => { setCreateMode(false); setNewCaseName(''); setNewCaseDesc('') }}
                    className="px-2 py-1.5 text-xs rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Search Bar ── */}
      <div className="flex-1 max-w-xl" ref={searchRef}>
        <div
          className={`flex items-center rounded border transition-colors ${
            activeCase
              ? 'bg-gray-800 border-gray-600 focus-within:border-cyan-500'
              : 'bg-gray-800/50 border-gray-700 opacity-50 cursor-not-allowed'
          }`}
        >
          {/* Search type toggle */}
          <select
            value={searchType}
            onChange={(e) => setSearchType(e.target.value)}
            disabled={!activeCase}
            className="bg-transparent text-xs text-gray-400 px-2 py-1.5 border-r border-gray-600 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
          >
            <option value="keyword">Company</option>
            <option value="piid">PIID</option>
          </select>

          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch(e)}
            disabled={!activeCase}
            placeholder={
              activeCase
                ? searchType === 'piid'
                  ? 'Search USASpending by PIID...'
                  : 'Search all sources...'
                : 'Select a case to search'
            }
            className="flex-1 bg-transparent text-xs text-white px-3 py-1.5 placeholder-gray-500 focus:outline-none disabled:cursor-not-allowed"
          />

          <button
            onClick={handleSearch}
            disabled={!activeCase || !searchQuery.trim()}
            className="px-3 py-1.5 text-xs text-cyan-400 hover:text-white disabled:text-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </div>
      </div>

      {/* ── Source Badges ── */}
      {sources && sources.length > 0 && (
        <div className="flex items-center gap-1.5 shrink-0">
          {applicableSources.map((s) => {
            const hasCredentials = !s.auth_required || sourceCredentials?.[s.id]
            return (
              <button
                key={s.id}
                onClick={() => s.auth_required && onSourceClick?.(s)}
                title={
                  hasCredentials
                    ? `${s.name}: Connected`
                    : `${s.name}: Click to add credentials`
                }
                className={`flex items-center gap-1.5 px-2 py-1 text-xs rounded-md border transition-all ${
                  hasCredentials
                    ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                    : 'bg-gray-800 border-gray-600 text-gray-500 hover:border-gray-500 hover:text-gray-400 cursor-pointer'
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${
                  hasCredentials ? 'bg-cyan-400' : 'bg-gray-600'
                }`} />
                <span className="truncate max-w-20">{s.name.replace('.gov', '')}</span>
              </button>
            )
          })}
        </div>
      )}

      {/* ── Right Controls ── */}
      <button
        onClick={onCompute}
        className="text-xs px-3 py-1.5 rounded bg-gray-800 hover:bg-gray-700 border border-gray-600 text-gray-300 hover:text-white transition-colors shrink-0"
      >
        Recompute
      </button>
    </div>
  )
}