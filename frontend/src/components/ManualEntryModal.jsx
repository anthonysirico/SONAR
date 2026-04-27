import { useState, useRef, useEffect, useCallback } from 'react'
import { fetchCaseNodes } from '../services/api'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const REL_TYPES = [
  'PRINCIPAL_OF', 'OFFICER_OF', 'SUBSIDIARY_OF', 'SUBCONTRACTOR_OF',
  'AWARDED_TO', 'ASSOCIATED_WITH', 'SHARES_ADDRESS_WITH',
]

export default function ManualEntryModal({ caseId, onClose, onSuccess }) {
  const [tab, setTab] = useState('form')
  const [entityType, setEntityType] = useState('company')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  // ── Company fields ──
  const [companyName, setCompanyName] = useState('')
  const [companyUei, setCompanyUei] = useState('')
  const [companyAddress, setCompanyAddress] = useState('')
  const [companyCity, setCompanyCity] = useState('')
  const [companyState, setCompanyState] = useState('')
  const [companyZip, setCompanyZip] = useState('')
  const [companyEntityType, setCompanyEntityType] = useState('')
  const [companyCage, setCompanyCage] = useState('')
  const [companyPhone, setCompanyPhone] = useState('')
  const [companyWebsite, setCompanyWebsite] = useState('')
  const [companyProfit, setCompanyProfit] = useState('')
  const [companyEin, setCompanyEin] = useState('')
  const [companyNotes, setCompanyNotes] = useState('')

  // ── Subcontractor fields ──
  const [isSub, setIsSub] = useState(false)
  const [billedAmount, setBilledAmount] = useState('')
  const [contractYear, setContractYear] = useState('')
  const [contractDesc, setContractDesc] = useState('')
  const [primeNodeId, setPrimeNodeId] = useState('')

  // ── Individual fields ──
  const [personName, setPersonName] = useState('')
  const [personTitle, setPersonTitle] = useState('')
  const [personEmail, setPersonEmail] = useState('')
  const [personPhone, setPersonPhone] = useState('')
  const [personComp, setPersonComp] = useState('')
  const [personNotes, setPersonNotes] = useState('')

  // ── Connections ──
  const [connections, setConnections] = useState([])

  // ── Node picker ──
  const [caseNodes, setCaseNodes] = useState([])
  const [nodeQuery, setNodeQuery] = useState('')
  const [pickerOpen, setPickerOpen] = useState(false)
  const [pickerTarget, setPickerTarget] = useState(null) // 'prime' | index

  // ── Upload ──
  const [uploadEntityType, setUploadEntityType] = useState('company')
  const [uploadResult, setUploadResult] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef(null)

  // Load case nodes for picker
  const loadNodes = useCallback(async (q = '') => {
    try {
      const nodes = await fetchCaseNodes(caseId, q)
      setCaseNodes(nodes)
    } catch { setCaseNodes([]) }
  }, [caseId])

  useEffect(() => { loadNodes() }, [loadNodes])

  const openPicker = (target) => {
    setPickerTarget(target)
    setPickerOpen(true)
    loadNodes()
  }

  const selectNode = (node) => {
    if (pickerTarget === 'prime') {
      setPrimeNodeId(node.node_id)
      setPickerOpen(false)
    } else if (typeof pickerTarget === 'number') {
      const updated = [...connections]
      updated[pickerTarget] = { ...updated[pickerTarget], target_node_id: node.node_id, target_name: node.name }
      setConnections(updated)
      setPickerOpen(false)
    }
  }

  const addConnection = () => {
    setConnections([...connections, { target_node_id: '', target_name: '', relationship_type: 'ASSOCIATED_WITH', notes: '' }])
  }

  const removeConnection = (i) => {
    setConnections(connections.filter((_, idx) => idx !== i))
  }

  const updateConnection = (i, field, value) => {
    const updated = [...connections]
    updated[i] = { ...updated[i], [field]: value }
    setConnections(updated)
  }

  // ── Submit handlers ──
  const handleSubmitCompany = async (e) => {
    e.preventDefault()
    if (!companyName.trim()) return
    setSubmitting(true); setError('')
    try {
      const res = await fetch(`${API}/api/cases/${caseId}/add-company`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: companyName.trim(), uei: companyUei.trim(), address: companyAddress.trim(),
          city: companyCity.trim(), state: companyState.trim(), zip_code: companyZip.trim(),
          entity_type: companyEntityType.trim(), cage_code: companyCage.trim(),
          phone: companyPhone.trim(), website: companyWebsite.trim(),
          profit_structure: companyProfit, ein: companyEin.trim(), notes: companyNotes.trim(),
          is_subcontractor: isSub, prime_contractor_node_id: primeNodeId,
          billed_amount: parseFloat(billedAmount) || 0, contract_year: contractYear,
          contract_description: contractDesc,
          connections: connections.filter(c => c.target_node_id),
        }),
      })
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Failed (${res.status})`)
      setResult(await res.json()); onSuccess?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  const handleSubmitIndividual = async (e) => {
    e.preventDefault()
    if (!personName.trim()) return
    setSubmitting(true); setError('')
    try {
      const res = await fetch(`${API}/api/cases/${caseId}/add-individual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: personName.trim(), title: personTitle.trim(), email: personEmail.trim(),
          phone: personPhone.trim(), compensation: parseFloat(personComp) || 0,
          notes: personNotes.trim(),
          connections: connections.filter(c => c.target_node_id),
        }),
      })
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Failed (${res.status})`)
      setResult(await res.json()); onSuccess?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  const handleUpload = async (file) => {
    if (!file) return
    setSubmitting(true); setError(''); setUploadResult(null)
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('entity_type', uploadEntityType)
      const res = await fetch(`${API}/api/cases/${caseId}/upload`, { method: 'POST', body: fd })
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `Upload failed (${res.status})`)
      setUploadResult(await res.json()); onSuccess?.()
    } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }

  // ── Node Picker Overlay ──
  const NodePicker = () => pickerOpen && (
    <div className="absolute inset-0 z-50 bg-gray-900/95 rounded-xl p-4 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400 font-medium">Select a Node</p>
        <button onClick={() => setPickerOpen(false)} className="text-gray-500 hover:text-white text-sm">✕</button>
      </div>
      <input
        autoFocus value={nodeQuery}
        onChange={(e) => { setNodeQuery(e.target.value); loadNodes(e.target.value) }}
        placeholder="Search nodes by name…"
        className="w-full px-2.5 py-2 text-xs bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 mb-3"
      />
      <div className="flex-1 overflow-y-auto space-y-1">
        {caseNodes.length === 0 && <p className="text-xs text-gray-600 text-center py-4">No nodes found</p>}
        {caseNodes.map((n) => (
          <button key={n.node_id} onClick={() => selectNode(n)}
            className="w-full text-left px-3 py-2 text-xs rounded-lg hover:bg-gray-800 border border-transparent hover:border-gray-600 transition-colors flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${n.type === 'Company' ? 'bg-sky-400' : n.type === 'Individual' ? 'bg-purple-400' : n.type === 'Contract' ? 'bg-emerald-400' : 'bg-orange-400'}`} />
            <span className="text-gray-300 truncate">{n.name}</span>
            <span className="text-gray-600 text-[10px] ml-auto shrink-0">{n.type}</span>
          </button>
        ))}
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        <div className="h-1 bg-linear-to-r from-cyan-500 via-blue-500 to-purple-500" />

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {['form', 'upload'].map(t => (
            <button key={t} onClick={() => { setTab(t); setResult(null); setError('') }}
              className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors ${tab === t ? 'text-cyan-400 border-b-2 border-cyan-400 bg-gray-800/50' : 'text-gray-400 hover:text-white'}`}>
              {t === 'form' ? 'Manual Entry' : 'Upload File'}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-5 relative">
          <NodePicker />

          {error && <div className="mb-4 px-3 py-2 bg-red-900/30 border border-red-700 rounded text-xs text-red-300">{error}</div>}
          {result && <div className="mb-4 px-3 py-2 bg-emerald-900/30 border border-emerald-700 rounded text-xs text-emerald-300">✓ Created "{result.name}" (node: {result.node_id?.slice(0, 8)}…)</div>}

          {/* ── Form Tab ── */}
          {tab === 'form' && (<>
            {/* Entity type selector */}
            <div className="flex gap-2 mb-4">
              {[['company', '🏢 Company'], ['individual', '👤 Individual']].map(([id, label]) => (
                <button key={id} onClick={() => { setEntityType(id); setResult(null); setConnections([]) }}
                  className={`flex-1 px-3 py-2 text-xs rounded-lg border transition-colors ${entityType === id ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-gray-800 border-gray-600 text-gray-400 hover:text-white'}`}>
                  {label}
                </button>
              ))}
            </div>

            {/* Company Form */}
            {entityType === 'company' && (
              <form onSubmit={handleSubmitCompany} className="space-y-3">
                <F label="Company Name *" value={companyName} onChange={setCompanyName} required />
                <div className="grid grid-cols-2 gap-3">
                  <F label="UEI" value={companyUei} onChange={setCompanyUei} placeholder="Auto-generated if blank" />
                  <F label="CAGE Code" value={companyCage} onChange={setCompanyCage} />
                </div>
                <F label="Street Address" value={companyAddress} onChange={setCompanyAddress} />
                <div className="grid grid-cols-3 gap-3">
                  <F label="City" value={companyCity} onChange={setCompanyCity} />
                  <F label="State" value={companyState} onChange={setCompanyState} />
                  <F label="ZIP" value={companyZip} onChange={setCompanyZip} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <F label="Phone" value={companyPhone} onChange={setCompanyPhone} />
                  <F label="Website" value={companyWebsite} onChange={setCompanyWebsite} />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <F label="Entity Type" value={companyEntityType} onChange={setCompanyEntityType} placeholder="e.g. LLC, Corp" />
                  <Sel label="Profit Structure" value={companyProfit} onChange={setCompanyProfit}
                    options={['', 'For-Profit', 'Non-Profit Organization', 'Government', 'Other']} />
                </div>
                <F label="EIN" value={companyEin} onChange={setCompanyEin} placeholder="XX-XXXXXXX" />

                {/* Subcontractor Section */}
                <div className="border-t border-gray-700 pt-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={isSub} onChange={(e) => setIsSub(e.target.checked)}
                      className="w-3.5 h-3.5 rounded border-gray-600 bg-gray-800 text-cyan-500 focus:ring-cyan-500" />
                    <span className="text-xs text-gray-400">This is a subcontractor</span>
                  </label>
                  {isSub && (
                    <div className="mt-3 space-y-3 pl-1 border-l-2 border-cyan-800 ml-1">
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Prime Contractor</label>
                        <button type="button" onClick={() => openPicker('prime')}
                          className="w-full px-2.5 py-2 text-xs bg-gray-800 border border-gray-600 rounded-lg text-left hover:border-cyan-500 transition-colors">
                          {primeNodeId ? <span className="text-cyan-400">{caseNodes.find(n => n.node_id === primeNodeId)?.name || primeNodeId.slice(0,12)+'…'}</span>
                            : <span className="text-gray-500">Click to select prime contractor…</span>}
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <F label="Billed Amount ($)" value={billedAmount} onChange={setBilledAmount} type="number" />
                        <F label="Contract Year" value={contractYear} onChange={setContractYear} placeholder="e.g. 2024" />
                      </div>
                      <F label="Contract Description" value={contractDesc} onChange={setContractDesc} />
                    </div>
                  )}
                </div>

                {/* Connections */}
                <ConnectionsSection connections={connections} onAdd={addConnection} onRemove={removeConnection}
                  onUpdate={updateConnection} onOpenPicker={openPicker} caseNodes={caseNodes} />

                <F label="Notes" value={companyNotes} onChange={setCompanyNotes} multiline />
                <BtnRow submitting={submitting} disabled={!companyName.trim()} label="Add Company" color="from-cyan-600 to-blue-600" onClose={onClose} />
              </form>
            )}

            {/* Individual Form */}
            {entityType === 'individual' && (
              <form onSubmit={handleSubmitIndividual} className="space-y-3">
                <F label="Full Name *" value={personName} onChange={setPersonName} required />
                <F label="Title / Role" value={personTitle} onChange={setPersonTitle} placeholder="e.g. CEO, CFO, Board Member" />
                <div className="grid grid-cols-2 gap-3">
                  <F label="Email" value={personEmail} onChange={setPersonEmail} />
                  <F label="Phone" value={personPhone} onChange={setPersonPhone} />
                </div>
                <F label="Compensation ($)" value={personComp} onChange={setPersonComp} type="number" />

                {/* Connections */}
                <ConnectionsSection connections={connections} onAdd={addConnection} onRemove={removeConnection}
                  onUpdate={updateConnection} onOpenPicker={openPicker} caseNodes={caseNodes} />

                <F label="Notes" value={personNotes} onChange={setPersonNotes} multiline />
                <BtnRow submitting={submitting} disabled={!personName.trim()} label="Add Person" color="from-purple-600 to-blue-600" onClose={onClose} />
              </form>
            )}
          </>)}

          {/* ── Upload Tab ── */}
          {tab === 'upload' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                {[['company', '🏢 Company'], ['individual', '👤 Individual']].map(([id, label]) => (
                  <button key={id} onClick={() => setUploadEntityType(id)}
                    className={`flex-1 px-3 py-2 text-xs rounded-lg border transition-colors ${uploadEntityType === id ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'bg-gray-800 border-gray-600 text-gray-400 hover:text-white'}`}>
                    {label}
                  </button>
                ))}
              </div>
              <div onDragOver={(e) => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer?.files?.[0]) }}
                onClick={() => fileRef.current?.click()}
                className={`flex flex-col items-center justify-center h-36 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${dragOver ? 'border-cyan-400 bg-cyan-500/10' : 'border-gray-600 hover:border-gray-500 bg-gray-800/30'}`}>
                <svg className="w-8 h-8 text-gray-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-xs text-gray-400">Drop <span className="text-cyan-400">.csv</span> or <span className="text-cyan-400">.xlsx</span> here</p>
                <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={(e) => handleUpload(e.target.files?.[0])} />
              </div>
              {submitting && <p className="text-xs text-cyan-400 animate-pulse">Uploading…</p>}
              {uploadResult && (
                <div className="p-3 bg-emerald-900/30 border border-emerald-700 rounded text-xs text-emerald-300 space-y-1">
                  <p>✓ Created {uploadResult.created} of {uploadResult.total_rows} {uploadResult.entity_type}(s)</p>
                  {uploadResult.errors?.length > 0 && uploadResult.errors.map((e, i) => <p key={i} className="text-red-300">Row {e.row}: {e.error}</p>)}
                </div>
              )}
              <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                <p className="text-xs text-gray-400 font-medium mb-1">Expected Columns</p>
                <p className="text-xs text-gray-500 font-mono leading-relaxed">
                  {uploadEntityType === 'company'
                    ? 'name, uei, address, city, state, zip_code, entity_type, cage_code, phone, website, ein, billed_amount, contract_year'
                    : 'name, title, email, phone, company_name, relationship_type, compensation'}
                </p>
              </div>
              <button onClick={onClose} className="w-full px-4 py-2 text-xs rounded-lg bg-gray-800 border border-gray-600 text-gray-300 hover:text-white transition-colors">Close</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Connections Section ──
function ConnectionsSection({ connections, onAdd, onRemove, onUpdate, onOpenPicker, caseNodes }) {
  return (
    <div className="border-t border-gray-700 pt-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-400 font-medium">Connect to Existing Nodes</p>
        <button type="button" onClick={onAdd}
          className="text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1">
          <span>+</span> Add Connection
        </button>
      </div>
      {connections.length === 0 && <p className="text-[10px] text-gray-600 mb-2">No connections added yet</p>}
      {connections.map((conn, i) => (
        <div key={i} className="flex gap-2 items-end mb-2">
          <div className="flex-1">
            <label className="block text-[10px] text-gray-500 mb-0.5">Target Node</label>
            <button type="button" onClick={() => onOpenPicker(i)}
              className="w-full px-2 py-1.5 text-xs bg-gray-800 border border-gray-600 rounded text-left hover:border-cyan-500 transition-colors truncate">
              {conn.target_name ? <span className="text-cyan-400">{conn.target_name}</span> : <span className="text-gray-500">Select…</span>}
            </button>
          </div>
          <div className="w-36">
            <label className="block text-[10px] text-gray-500 mb-0.5">Relationship</label>
            <select value={conn.relationship_type} onChange={(e) => onUpdate(i, 'relationship_type', e.target.value)}
              className="w-full px-2 py-1.5 text-xs bg-gray-800 border border-gray-600 rounded text-white focus:outline-none">
              {REL_TYPES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <button type="button" onClick={() => onRemove(i)} className="text-gray-600 hover:text-red-400 text-sm pb-1">✕</button>
        </div>
      ))}
    </div>
  )
}

// ── Reusable form primitives ──
function F({ label, value, onChange, placeholder, required, multiline, type = 'text' }) {
  const cls = "w-full px-2.5 py-2 text-xs bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-all"
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {multiline
        ? <textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={2} className={cls + ' resize-none'} />
        : <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} required={required} className={cls} />}
    </div>
  )
}

function Sel({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-2.5 py-2 text-xs bg-gray-800 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-cyan-500 transition-all">
        {options.map(o => <option key={o} value={o}>{o || '— Select —'}</option>)}
      </select>
    </div>
  )
}

function BtnRow({ submitting, disabled, label, color, onClose }) {
  return (
    <div className="flex gap-2 pt-2">
      <button type="submit" disabled={disabled || submitting}
        className={`flex-1 px-4 py-2 text-xs rounded-lg bg-linear-to-r ${color} hover:brightness-110 disabled:from-gray-700 disabled:to-gray-700 disabled:text-gray-500 text-white font-medium transition-all`}>
        {submitting ? 'Creating…' : label}
      </button>
      <button type="button" onClick={onClose} className="px-4 py-2 text-xs rounded-lg bg-gray-800 border border-gray-600 text-gray-300 hover:text-white transition-colors">Close</button>
    </div>
  )
}
