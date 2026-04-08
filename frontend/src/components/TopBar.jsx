export default function TopBar({ onCompute }) {
  return (
    <div className="flex items-center justify-between px-6 py-3 bg-gray-900 border-b border-gray-700">
      <div className="flex items-center gap-3">
        <span className="text-cyan-400 font-bold text-xl tracking-widest">SONAR</span>
        <span className="text-gray-500 text-xs tracking-wider uppercase">
          Suspicious Organization and Network Analysis & Reporting
        </span>
      </div>
      <button
        onClick={onCompute}
        className="text-xs px-3 py-1 rounded bg-cyan-800 hover:bg-cyan-600 text-white transition-colors"
      >
        Recompute Prominence
      </button>
    </div>
  )
}