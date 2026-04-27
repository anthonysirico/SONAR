import { useState, useMemo, useEffect, useCallback } from 'react'
import { updateNode, deleteNode, fetchNodeRelationships, addNodeRelationship, deleteNodeRelationship, fetchCaseNodes } from '../services/api'

const REL_TYPES = [
  'PRINCIPAL_OF', 'OFFICER_OF', 'SUBSIDIARY_OF', 'SUBCONTRACTOR_OF',
  'AWARDED_TO', 'ASSOCIATED_WITH', 'SHARES_ADDRESS_WITH',
]

const GMAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY || ''

const RISK_COLORS = {
  high:     'text-red-400',
  elevated: 'text-orange-400',
  watch:    'text-yellow-400',
  baseline: 'text-gray-400',
}

const FLAG_LABELS = {
  SHELL_CLUSTER:             { label: 'Shell Cluster',             color: 'bg-red-900 text-red-300' },
  REVOLVING_DOOR:            { label: 'Revolving Door',            color: 'bg-orange-900 text-orange-300' },
  SPLIT_AWARD:               { label: 'Split Award',              color: 'bg-yellow-900 text-yellow-300' },
  EXCLUSION_EVASION:         { label: 'Exclusion Evasion',        color: 'bg-red-900 text-red-300' },
  SOLE_SOURCE_CONCENTRATION: { label: 'Sole Source Concentration', color: 'bg-amber-900 text-amber-300' },
  NONPROFIT_REVENUE_ANOMALY: { label: 'NP Revenue Anomaly',       color: 'bg-rose-900 text-rose-300' },
  EXEC_COMP_OUTLIER:         { label: 'Exec Comp Outlier',        color: 'bg-fuchsia-900 text-fuchsia-300' },
  NONPROFIT_SOLE_SOURCE:     { label: 'NP Sole Source',           color: 'bg-pink-900 text-pink-300' },
}

// Attributes to hide from the raw list (displayed in dedicated sections)
const HIDDEN_KEYS = new Set([
  'id', 'label', 'type', 'color', 'size',
  'prominence_score', 'prominence_factors',
  'wfa_flags', 'wfa_explanations', 'wfa_confidence',
  'exclusion_flag',
])

// System-computed fields that should not be editable
const SYSTEM_KEYS = new Set([
  'node_id', 'prominence_score', 'prominence_factors',
  'wfa_flags', 'wfa_explanations', 'wfa_confidence',
  'auto_enriched', 'id', 'label', 'type', 'color', 'size',
])

function getRiskTier(score) {
  if (score >= 0.75) return { label: 'CRITICAL',  color: RISK_COLORS.high }
  if (score >= 0.50) return { label: 'ELEVATED',  color: RISK_COLORS.elevated }
  if (score >= 0.25) return { label: 'WATCH',     color: RISK_COLORS.watch }
  return               { label: 'BASELINE',  color: RISK_COLORS.baseline }
}

export default function NodeDetail({ node, caseId, onClose, onRefresh }) {
  if (!node) return null

  const data = node.data()
  const score = data.prominence_score ?? 0
  const tier = getRiskTier(score)

  // Parse arrays that may come as strings from Cytoscape
  const prominenceFactors = parseArray(data.prominence_factors)
  const wfaFlags = parseArray(data.wfa_flags)
  const wfaExplanations = parseArray(data.wfa_explanations)

  // ── Edit state ──
  const [editing, setEditing] = useState(false)
  const [editFields, setEditFields] = useState({})
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState('')
  const [editSuccess, setEditSuccess] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(false)

  // ── Relationship state ──
  const [rels, setRels] = useState([])
  const [relsLoading, setRelsLoading] = useState(false)
  const [showAddConn, setShowAddConn] = useState(false)
  const [caseNodes, setCaseNodes] = useState([])
  const [nodeSearch, setNodeSearch] = useState('')
  const [newConnTarget, setNewConnTarget] = useState(null)
  const [newConnType, setNewConnType] = useState('ASSOCIATED_WITH')
  const [newConnDir, setNewConnDir] = useState('outgoing')

  const loadRels = useCallback(async () => {
    if (!caseId || !data.node_id) return
    setRelsLoading(true)
    try {
      const r = await fetchNodeRelationships(caseId, data.node_id)
      setRels(r)
    } catch { setRels([]) }
    finally { setRelsLoading(false) }
  }, [caseId, data.node_id])

  const loadNodes = useCallback(async (q = '') => {
    if (!caseId) return
    try { setCaseNodes(await fetchCaseNodes(caseId, q)) } catch { setCaseNodes([]) }
  }, [caseId])

  const editableEntries = useMemo(() => {
    return Object.entries(data).filter(([key]) => {
      if (HIDDEN_KEYS.has(key)) return false
      if (SYSTEM_KEYS.has(key)) return false
      return true
    })
  }, [data])

  const startEditing = () => {
    const fields = {}
    editableEntries.forEach(([key, val]) => {
      fields[key] = val === null || val === undefined ? '' : String(val)
    })
    setEditFields(fields)
    setEditing(true)
    setEditError('')
    setEditSuccess('')
    loadRels()
    loadNodes()
  }

  const cancelEditing = () => {
    setEditing(false)
    setEditFields({})
    setEditError('')
    setConfirmDelete(false)
    setShowAddConn(false)
    setNewConnTarget(null)
  }

  const handleDisconnect = async (relId) => {
    if (!caseId || !data.node_id) return
    setSaving(true)
    try {
      await deleteNodeRelationship(caseId, data.node_id, relId)
      setRels(rels.filter(r => r.rel_id !== relId))
      onRefresh?.()
    } catch (e) { setEditError(e.message) }
    finally { setSaving(false) }
  }

  const handleAddConnection = async () => {
    if (!caseId || !data.node_id || !newConnTarget) return
    setSaving(true)
    try {
      await addNodeRelationship(caseId, data.node_id, {
        target_node_id: newConnTarget.node_id,
        relationship_type: newConnType,
        direction: newConnDir,
      })
      setShowAddConn(false)
      setNewConnTarget(null)
      setNewConnType('ASSOCIATED_WITH')
      await loadRels()
      onRefresh?.()
    } catch (e) { setEditError(e.message) }
    finally { setSaving(false) }
  }

  const handleSave = async () => {
    if (!caseId || !data.node_id) return
    setSaving(true)
    setEditError('')
    try {
      await updateNode(caseId, data.node_id, editFields)
      setEditSuccess('Saved')
      setEditing(false)
      setTimeout(() => setEditSuccess(''), 2000)
      onRefresh?.()
    } catch (e) {
      setEditError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!caseId || !data.node_id) return
    setSaving(true)
    try {
      await deleteNode(caseId, data.node_id)
      onClose()
      onRefresh?.()
    } catch (e) {
      setEditError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-gray-900 border-l border-gray-700 p-5 overflow-y-auto z-10">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">
            {data.type || 'Node'}
          </p>
          <h2 className="text-white font-semibold text-sm mt-1">
            {data.label || data.node_id}
          </h2>
        </div>
        <div className="flex items-center gap-1.5">
          {/* Edit button */}
          {caseId && !editing && (
            <button
              onClick={startEditing}
              title="Edit node"
              className="text-gray-500 hover:text-cyan-400 transition-colors p-1"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          )}
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white text-lg leading-none"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Edit success */}
      {editSuccess && (
        <div className="mb-3 px-3 py-1.5 bg-emerald-900/30 border border-emerald-700 rounded text-xs text-emerald-300">
          ✓ {editSuccess}
        </div>
      )}

      {/* ── EDIT MODE ── */}
      {editing && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs text-cyan-400 font-medium uppercase tracking-wider">Edit Mode</p>
          </div>

          {editError && (
            <div className="mb-3 px-3 py-1.5 bg-red-900/30 border border-red-700 rounded text-xs text-red-300">{editError}</div>
          )}

          <div className="space-y-2">
            {editableEntries.map(([key]) => (
              <div key={key}>
                <label className="block text-[10px] text-gray-500 uppercase mb-0.5">
                  {key.replace(/_/g, ' ')}
                </label>
                <input
                  type="text"
                  value={editFields[key] ?? ''}
                  onChange={(e) => setEditFields({ ...editFields, [key]: e.target.value })}
                  className="w-full px-2 py-1.5 text-xs bg-gray-800 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-all"
                />
              </div>
            ))}
          </div>

          <div className="flex gap-2 mt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 px-3 py-2 text-xs rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 text-white font-medium transition-colors"
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
            <button
              onClick={cancelEditing}
              className="px-3 py-2 text-xs rounded-lg bg-gray-800 border border-gray-600 text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>

          {/* ── Connections ── */}
          <div className="mt-4 pt-3 border-t border-gray-700">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-gray-400 font-medium uppercase tracking-wider">Connections</p>
              <button type="button" onClick={() => { setShowAddConn(!showAddConn); if (!showAddConn) loadNodes() }}
                className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
                <span>{showAddConn ? '−' : '+'}</span> {showAddConn ? 'Cancel' : 'Add'}
              </button>
            </div>

            {/* Existing relationships */}
            {relsLoading && <p className="text-[10px] text-gray-600 animate-pulse">Loading…</p>}
            {!relsLoading && rels.length === 0 && <p className="text-[10px] text-gray-600 mb-2">No connections</p>}
            <div className="space-y-1 mb-3 max-h-40 overflow-y-auto">
              {rels.map((r) => (
                <div key={r.rel_id} className="flex items-center gap-2 text-xs px-2 py-1.5 rounded bg-gray-800 border border-gray-700 group">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    r.other_type === 'Company' ? 'bg-sky-400' : r.other_type === 'Individual' ? 'bg-purple-400' : 'bg-orange-400'
                  }`} />
                  <span className="text-gray-400 truncate flex-1">
                    <span className="text-gray-500 text-[10px]">{r.is_outgoing ? '→' : '←'}</span>{' '}
                    <span className="text-gray-300">{r.other_name}</span>
                  </span>
                  <span className="text-[10px] text-gray-600 shrink-0">{r.rel_type}</span>
                  <button onClick={() => handleDisconnect(r.rel_id)} title="Disconnect"
                    className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all text-sm leading-none shrink-0">
                    ✕
                  </button>
                </div>
              ))}
            </div>

            {/* Add connection picker */}
            {showAddConn && (
              <div className="p-3 rounded-lg bg-gray-800 border border-gray-700 space-y-2">
                <input
                  autoFocus
                  value={nodeSearch}
                  onChange={(e) => { setNodeSearch(e.target.value); loadNodes(e.target.value) }}
                  placeholder="Search nodes…"
                  className="w-full px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
                />
                <div className="max-h-32 overflow-y-auto space-y-0.5">
                  {caseNodes.filter(n => n.node_id !== data.node_id).map((n) => (
                    <button key={n.node_id} onClick={() => setNewConnTarget(n)}
                      className={`w-full text-left px-2 py-1 text-xs rounded flex items-center gap-2 transition-colors ${
                        newConnTarget?.node_id === n.node_id ? 'bg-cyan-900/40 border border-cyan-700' : 'hover:bg-gray-700 border border-transparent'
                      }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        n.type === 'Company' ? 'bg-sky-400' : n.type === 'Individual' ? 'bg-purple-400' : 'bg-orange-400'
                      }`} />
                      <span className="text-gray-300 truncate">{n.name}</span>
                      <span className="text-[10px] text-gray-600 ml-auto">{n.type}</span>
                    </button>
                  ))}
                  {caseNodes.filter(n => n.node_id !== data.node_id).length === 0 && (
                    <p className="text-[10px] text-gray-600 text-center py-2">No nodes found</p>
                  )}
                </div>
                {newConnTarget && (
                  <div className="pt-2 border-t border-gray-700 space-y-2">
                    <p className="text-[10px] text-gray-400">Connect to <span className="text-cyan-400">{newConnTarget.name}</span></p>
                    <div className="flex gap-2">
                      <select value={newConnType} onChange={(e) => setNewConnType(e.target.value)}
                        className="flex-1 px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white focus:outline-none">
                        {REL_TYPES.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                      <select value={newConnDir} onChange={(e) => setNewConnDir(e.target.value)}
                        className="w-24 px-2 py-1.5 text-xs bg-gray-900 border border-gray-600 rounded text-white focus:outline-none">
                        <option value="outgoing">→ Out</option>
                        <option value="incoming">← In</option>
                      </select>
                    </div>
                    <button onClick={handleAddConnection} disabled={saving}
                      className="w-full px-3 py-1.5 text-xs rounded bg-cyan-700 hover:bg-cyan-600 text-white font-medium transition-colors disabled:bg-gray-700">
                      {saving ? 'Connecting…' : 'Connect'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Delete */}
          <div className="mt-4 pt-3 border-t border-gray-800">
            {!confirmDelete ? (
              <button
                onClick={() => setConfirmDelete(true)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-red-800 text-red-400 hover:bg-red-900/30 transition-colors"
              >
                Delete This Node
              </button>
            ) : (
              <div className="space-y-2">
                <p className="text-xs text-red-300">This will permanently remove this node and all its relationships.</p>
                <div className="flex gap-2">
                  <button
                    onClick={handleDelete}
                    disabled={saving}
                    className="flex-1 px-3 py-2 text-xs rounded-lg bg-red-700 hover:bg-red-600 text-white font-medium transition-colors"
                  >
                    {saving ? 'Deleting…' : 'Confirm Delete'}
                  </button>
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-3 py-2 text-xs rounded-lg bg-gray-800 border border-gray-600 text-gray-300 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── READ MODE (shown when not editing) ── */}
      {!editing && (<>

      {/* Risk Tier */}
      <div className="mb-4 p-3 rounded bg-gray-800">
        <div className="flex items-center justify-between mb-1">
          <p className="text-xs text-gray-500">Risk Tier</p>
          <p className={`font-bold text-sm ${tier.color}`}>{tier.label}</p>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-1.5 mt-1">
          <div
            className="h-1.5 rounded-full transition-all"
            style={{
              width: `${Math.min(score * 100, 100)}%`,
              backgroundColor: score >= 0.75 ? '#ef4444' : score >= 0.50 ? '#f97316' : score >= 0.25 ? '#eab308' : '#6b7280',
            }}
          />
        </div>
        <p className="text-gray-500 text-xs mt-1.5 text-right">
          {score.toFixed(4)}
        </p>
      </div>

      {/* Prominence Explanation */}
      {prominenceFactors.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Why this score</p>
          <div className="space-y-1.5">
            {prominenceFactors.map((factor, i) => (
              <div key={i} className="text-xs text-gray-400 pl-2 border-l-2 border-gray-700">
                {factor}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* WFA Flags */}
      {wfaFlags.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">WFA Flags</p>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {wfaFlags.map((flag, i) => {
              const meta = FLAG_LABELS[flag] || { label: flag, color: 'bg-gray-800 text-gray-400' }
              return (
                <span key={i} className={`text-xs px-2 py-0.5 rounded ${meta.color}`}>
                  {meta.label}
                </span>
              )
            })}
          </div>
          {data.wfa_confidence != null && (
            <p className="text-xs text-gray-500">
              Detection confidence: {Number(data.wfa_confidence).toFixed(2)}
            </p>
          )}
        </div>
      )}

      {/* WFA Explanations */}
      {wfaExplanations.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Detection Analysis</p>
          <div className="space-y-2">
            {wfaExplanations.map((explanation, i) => (
              <div key={i} className="text-xs text-gray-300 p-2.5 rounded bg-gray-800 border border-gray-700 leading-relaxed">
                {explanation}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Exclusion Flag */}
      {(data.exclusion_flag === 'true' || data.exclusion_flag === true) && (
        <div className="mb-4 p-2.5 rounded bg-red-900/50 border border-red-700">
          <p className="text-red-400 text-xs font-bold">⚠ EXCLUSION FLAG ACTIVE</p>
          <p className="text-red-300 text-xs mt-1">
            This entity is on the SAM.gov exclusion list.
          </p>
        </div>
      )}

      {/* Google Maps — Street View & Satellite (Companies with address) */}
      {data.address && data.address.length > 5 && (
        <AddressVerification address={data.address} label={data.label} />
      )}

      {/* Nonprofit 990 Financial Data */}
      {(data.nonprofit_status === true || data.nonprofit_status === 'true') && (
        <div className="mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">990 Nonprofit Financials</p>
          <div className="p-3 rounded bg-gray-800 space-y-2">
            {data.profit_structure && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Structure</span>
                <span className="text-emerald-400 font-medium">{data.profit_structure}</span>
              </div>
            )}
            {data.total_990_revenue != null && Number(data.total_990_revenue) > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">990 Revenue</span>
                <span className="text-gray-300">${Number(data.total_990_revenue).toLocaleString()}</span>
              </div>
            )}
            {data.total_990_expenses != null && Number(data.total_990_expenses) > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">990 Expenses</span>
                <span className="text-gray-300">${Number(data.total_990_expenses).toLocaleString()}</span>
              </div>
            )}
            {data.total_990_assets != null && Number(data.total_990_assets) > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Total Assets</span>
                <span className="text-gray-300">${Number(data.total_990_assets).toLocaleString()}</span>
              </div>
            )}
            {data.total_officer_compensation != null && Number(data.total_officer_compensation) > 0 && (
              <>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Officer Compensation</span>
                  <span className={`font-medium ${
                    Number(data.officer_comp_pct) > 0.20 ? 'text-red-400' : 'text-gray-300'
                  }`}>
                    ${Number(data.total_officer_compensation).toLocaleString()}
                  </span>
                </div>
                {data.officer_comp_pct != null && Number(data.officer_comp_pct) > 0 && (
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-500">Comp/Revenue Ratio</span>
                    <span className={`font-medium ${
                      Number(data.officer_comp_pct) > 0.20 ? 'text-red-400' : 'text-gray-300'
                    }`}>
                      {(Number(data.officer_comp_pct) * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </>
            )}
            {data.latest_990_year != null && Number(data.latest_990_year) > 0 && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Latest 990 Year</span>
                <span className="text-gray-400">{data.latest_990_year}</span>
              </div>
            )}
            {data.ein && (
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">EIN</span>
                <span className="text-gray-400 font-mono">{data.ein}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Attributes */}
      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Attributes</p>
        {Object.entries(data).map(([key, val]) => {
          if (HIDDEN_KEYS.has(key)) return null
          if (val === '' || val === null || val === undefined) return null
          return (
            <div key={key} className="flex justify-between text-xs gap-2">
              <span className="text-gray-500 capitalize shrink-0">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-gray-300 text-right wrap-break-word min-w-0">
                {Array.isArray(val) ? val.join(', ') : String(val)}
              </span>
            </div>
          )
        })}
      </div>
      </>)}
    </div>
  )
}

// ─── Address Verification (Google Maps) ─────────────────────

function AddressVerification({ address, label }) {
  const [mapView, setMapView] = useState('street') // 'street' | 'satellite'
  const encodedAddr = encodeURIComponent(address)

  // Google Maps Embed API (free tier, no billing required)
  const streetViewUrl = GMAPS_API_KEY
    ? `https://www.google.com/maps/embed/v1/streetview?key=${GMAPS_API_KEY}&location=${encodedAddr}&heading=210&pitch=10&fov=75`
    : null
  const satelliteUrl = GMAPS_API_KEY
    ? `https://www.google.com/maps/embed/v1/place?key=${GMAPS_API_KEY}&q=${encodedAddr}&maptype=satellite&zoom=18`
    : null
  const placeUrl = GMAPS_API_KEY
    ? `https://www.google.com/maps/embed/v1/place?key=${GMAPS_API_KEY}&q=${encodedAddr}&zoom=16`
    : null

  // Fallback: direct Google Maps links (always work, no API key needed)
  const gmapsLink = `https://www.google.com/maps/search/?api=1&query=${encodedAddr}`
  const streetViewLink = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${encodedAddr}`

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider">Address Verification</p>
        <div className="flex gap-0.5 bg-gray-800 rounded-md p-0.5">
          <button
            onClick={() => setMapView('street')}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              mapView === 'street'
                ? 'bg-cyan-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Street
          </button>
          <button
            onClick={() => setMapView('satellite')}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              mapView === 'satellite'
                ? 'bg-cyan-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Satellite
          </button>
          <button
            onClick={() => setMapView('map')}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              mapView === 'map'
                ? 'bg-cyan-700 text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Map
          </button>
        </div>
      </div>

      {/* Map iframe */}
      {GMAPS_API_KEY ? (
        <div className="rounded-lg overflow-hidden border border-gray-700 bg-gray-800">
          <iframe
            key={mapView}
            width="100%"
            height="200"
            style={{ border: 0 }}
            loading="lazy"
            allowFullScreen
            referrerPolicy="no-referrer-when-downgrade"
            src={
              mapView === 'street' ? streetViewUrl :
              mapView === 'satellite' ? satelliteUrl :
              placeUrl
            }
          />
        </div>
      ) : (
        <div className="rounded-lg border border-gray-700 bg-gray-800 p-4 text-center">
          <p className="text-xs text-gray-500 mb-2">Google Maps API key not configured</p>
          <a
            href={mapView === 'street' ? streetViewLink : gmapsLink}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 underline"
          >
            Open in Google Maps ↗
          </a>
        </div>
      )}

      <p className="text-xs text-gray-600 mt-1.5 truncate" title={address}>
        📍 {address}
      </p>
    </div>
  )
}

// Helper: Cytoscape sometimes stores arrays as strings
function parseArray(val) {
  if (!val) return []
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try { return JSON.parse(val) } catch { return [] }
  }
  return []
}