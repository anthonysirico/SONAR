const RISK_COLORS = {
  high:     'text-red-400',
  elevated: 'text-orange-400',
  watch:    'text-yellow-400',
  baseline: 'text-gray-400',
}

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

  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-gray-900 border-l border-gray-700 p-5 overflow-y-auto z-10">
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
          className="text-gray-500 hover:text-white text-lg"
        >
          ✕
        </button>
      </div>

      {/* Risk Tier */}
      <div className="mb-4 p-3 rounded bg-gray-800">
        <p className="text-xs text-gray-500 mb-1">Risk Tier</p>
        <p className={`font-bold text-sm ${tier.color}`}>{tier.label}</p>
        <p className="text-gray-400 text-xs mt-1">
          Prominence Score: {score.toFixed(4)}
        </p>
      </div>

      {/* Attributes */}
      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Attributes</p>
        {Object.entries(data).map(([key, val]) => {
          if (['id', 'label', 'type', 'color', 'size'].includes(key)) return null
          return (
            <div key={key} className="flex justify-between text-xs">
              <span className="text-gray-500 capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-gray-300 text-right max-w-[55%] break-words">
                {Array.isArray(val) ? val.join(', ') : String(val)}
              </span>
            </div>
          )
        })}
      </div>

      {/* Exclusion Flag */}
      {data.exclusion_flag === 'true' || data.exclusion_flag === true ? (
        <div className="mt-4 p-2 rounded bg-red-900 border border-red-600">
          <p className="text-red-400 text-xs font-bold">⚠ EXCLUSION FLAG ACTIVE</p>
          <p className="text-red-300 text-xs mt-1">
            This entity is on the SAM.gov exclusion list.
          </p>
        </div>
      ) : null}
    </div>
  )
}