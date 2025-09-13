import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '' // same origin by default

export default function App() {
  const [file, setFile] = useState(null)
  const [presets, setPresets] = useState([])
  const [preset, setPreset] = useState('')
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const [error, setError] = useState(null)
  const [totalChunks, setTotalChunks] = useState(null)
  const [processedChunks, setProcessedChunks] = useState(null)

  // Load voice presets from API
  useEffect(() => {
    const load = async () => {
      try {
        const r = await fetch(`${API_URL}/voices`)
        if (!r.ok) throw new Error('Failed to load voices')
        const data = await r.json()
        const ps = Array.isArray(data.presets) ? data.presets : []
        setPresets(ps)
        if (ps.length && !preset) setPreset(ps[0])
      } catch (e) {
        console.error(e)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if (!jobId) return
    const t = setInterval(async () => {
      try {
        const r = await fetch(`${API_URL}/tts/${jobId}`)
        if (!r.ok) throw new Error('Failed to fetch status')
        const data = await r.json()
        setStatus(data.status)
        setTotalChunks(data.total_chunks ?? null)
        setProcessedChunks(data.processed_chunks ?? null)
        if (data.status === 'finished' && data.audio_url) {
          const resolveUrl = (u) => {
            if (!u) return null
            if (/^https?:\/\//i.test(u)) return u
            const base = (API_URL || '').replace(/\/+$/, '')
            const path = u.startsWith('/') ? u : `/${u}`
            return `${base}${path}`
          }
          setAudioUrl(resolveUrl(data.audio_url))
          clearInterval(t)
        }
        if (data.status === 'failed') {
          setError(data.error || 'Job failed')
          clearInterval(t)
        }
      } catch (e) {
        console.error(e)
      }
    }, 1500)
    return () => clearInterval(t)
  }, [jobId])

  const onSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setStatus(null)
    setAudioUrl(null)
    setJobId(null)
    setTotalChunks(null)
    setProcessedChunks(null)
    if (!file) {
      setError('Please select a file')
      return
    }
    const form = new FormData()
    form.append('file', file)
    form.append('preset', preset)
    try {
      const r = await fetch(`${API_URL}/tts`, { method: 'POST', body: form })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      setJobId(data.job_id)
      setStatus(data.status)
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: '2rem auto', fontFamily: 'system-ui, sans-serif' }}>
      <h1>Document → Speech</h1>
      <p>Upload .pdf, .docx, or .txt and generate audio using VibeVoice.</p>
      <form onSubmit={onSubmit}>
        <div style={{ margin: '1rem 0' }}>
          <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </div>
        <div style={{ margin: '1rem 0' }}>
          <label>Voice preset: </label>
          <select value={preset} onChange={(e) => setPreset(e.target.value)} disabled={!presets.length}>
            {presets.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <button type="submit">Generate Audio</button>
      </form>
      {status && <p>Status: <strong>{status}</strong></p>}
      {(status === 'queued' || status === 'started' || status === 'running') && totalChunks && (
        <div style={{ margin: '0.5rem 0' }}>
          <div style={{ marginBottom: 4 }}>Progress: {processedChunks ?? 0} / {totalChunks}</div>
          <progress value={processedChunks ?? 0} max={totalChunks} style={{ width: '100%' }} />
        </div>
      )}
      {error && <p style={{ color: 'crimson' }}>Error: {error}</p>}
      {audioUrl && (
        <div style={{ marginTop: '1rem' }}>
          <audio controls src={audioUrl} style={{ width: '100%' }} />
          <div style={{ marginTop: '0.5rem' }}>
            <a href={audioUrl} download>Download MP3</a>
          </div>
        </div>
      )}
    </div>
  )
}
