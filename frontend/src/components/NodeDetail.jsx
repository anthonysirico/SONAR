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
}

// Attributes to hide from the raw list (displayed in dedicated sections)
const HIDDEN_KEYS = new Set([
  'id', 'label', 'type', 'color', 'size',
  'prominence_score', 'prominence_factors',
  'wfa_flags', 'wfa_explanations', 'wfa_confidence',
  'exclusion_flag',
])

function getRiskTier(score) {
  if (score >= 0.75) return { label: 'CRITICAL',  color: RISK_COLORS.high }
  if (score >= 0.50) return { label: 'ELEVATED',  color: RISK_COLORS.elevated }
  if (score >= 0.25) return { label: 'WATCH',     color: RISK_COLORS.watch }
  return               { label: 'BASELINE',  color: RISK_COLORS.baseline }
}

export default function NodeDetail({ node, onClose }) {
  if (!node) return null

  const data = node.data()
  const score = data.prominence_score ?? 0
  const tier = getRiskTier(score)

  // Parse arrays that may come as strings from Cytoscape
  const prominenceFactors = parseArray(data.prominence_factors)
  const wfaFlags = parseArray(data.wfa_flags)
  const wfaExplanations = parseArray(data.wfa_explanations)

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
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white text-lg leading-none"
        >
          ✕
        </button>
      </div>

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