import { useState, useRef, useEffect } from 'react'

export default function CredentialModal({ source, onSubmit, onClose }) {
  const [apiKey, setApiKey] = useState('')
  const [validating, setValidating] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Close on Escape
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!apiKey.trim()) return
    onSubmit(source.id, { api_key: apiKey.trim() })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden">

        {/* Header gradient accent */}
        <div className="h-1 bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500" />

        <div className="p-6">
          {/* Icon + Title */}
          <div className="flex items-start gap-4 mb-5">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
            <div>
              <h3 className="text-white text-sm font-semibold">{source?.name} Credentials</h3>
              <p className="text-gray-400 text-xs mt-0.5">
                {source?.description}
              </p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit}>
            <label className="block text-xs text-gray-400 mb-1.5 font-medium">
              API Key
            </label>
            <input
              ref={inputRef}
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your SAM.gov API key"
              className="w-full px-3 py-2.5 text-sm bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 transition-all"
            />
            <p className="text-xs text-gray-500 mt-2">
              Obtain your key from{' '}
              <span className="text-cyan-400">sam.gov/profile/details</span>
              {' '}→ Public API Key. Stored in session only.
            </p>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-600 text-gray-300 hover:text-white transition-all"
              >
                Skip
              </button>
              <button
                type="submit"
                disabled={!apiKey.trim() || validating}
                className="px-5 py-2 text-xs rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 text-white font-medium transition-all shadow-lg shadow-cyan-500/20 disabled:shadow-none"
              >
                {validating ? 'Validating...' : 'Connect'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
