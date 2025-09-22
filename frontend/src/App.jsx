import React, { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || '' // same origin by default

export default function App() {
  const [file, setFile] = useState(null)
  const [presets, setPresets] = useState([])
  const [preset, setPreset] = useState('')
  const [jobId, setJobId] = useState(() => localStorage.getItem('tts-job-id') || null)
  const [status, setStatus] = useState(() => localStorage.getItem('tts-status') || null)
  const [audioUrl, setAudioUrl] = useState(() => localStorage.getItem('tts-audio-url') || null)
  const [error, setError] = useState(null)
  const [totalChunks, setTotalChunks] = useState(null)
  const [processedChunks, setProcessedChunks] = useState(null)
  const [filename, setFilename] = useState(() => localStorage.getItem('tts-filename') || null)

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
          const resolvedUrl = resolveUrl(data.audio_url)
          setAudioUrl(resolvedUrl)
          // Persist to localStorage
          localStorage.setItem('tts-status', data.status)
          localStorage.setItem('tts-audio-url', resolvedUrl)
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
      setFilename(file.name)
      // Persist to localStorage
      localStorage.setItem('tts-job-id', data.job_id)
      localStorage.setItem('tts-status', data.status)
      localStorage.setItem('tts-filename', file.name)
    } catch (e) {
      setError(String(e))
    }
  }

  const clearState = () => {
    setJobId(null)
    setStatus(null)
    setAudioUrl(null)
    setError(null)
    setTotalChunks(null)
    setProcessedChunks(null)
    setFilename(null)
    localStorage.removeItem('tts-job-id')
    localStorage.removeItem('tts-status')
    localStorage.removeItem('tts-audio-url')
    localStorage.removeItem('tts-filename')
  }

  const getDownloadUrl = (audioUrl) => {
    if (!audioUrl) return null
    // Extract filename from audioUrl (e.g., /files/filename.mp3)
    const urlFilename = audioUrl.split('/').pop()
    const base = (API_URL || '').replace(/\/+$/, '')
    return `${base}/download/${urlFilename}`
  }

  const copyFilePath = () => {
    if (!audioUrl) return
    const urlFilename = audioUrl.split('/').pop()
    const filePath = `/Users/my_studio/proj/projects/tts/storage/${urlFilename}`
    navigator.clipboard.writeText(filePath)
    alert('File path copied to clipboard!')
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
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button type="submit">Generate Audio</button>
          {(audioUrl || status) && (
            <button type="button" onClick={clearState} style={{ backgroundColor: '#f44336', color: 'white' }}>
              Clear Results
            </button>
          )}
        </div>
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
        <div style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '4px' }}>
          <h3>✅ Audio Generated Successfully!</h3>
          {filename && <p><strong>File:</strong> {filename}</p>}
          <audio controls src={audioUrl} style={{ width: '100%' }} />
          <div style={{ marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <a 
              href={getDownloadUrl(audioUrl)} 
              download
              style={{ 
                backgroundColor: '#4CAF50', 
                color: 'white', 
                padding: '8px 16px', 
                textDecoration: 'none', 
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              📥 Download MP3
            </a>
            <button 
              onClick={copyFilePath}
              style={{ 
                backgroundColor: '#2196F3', 
                color: 'white', 
                padding: '8px 16px', 
                border: 'none', 
                borderRadius: '4px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              📋 Copy File Path
            </button>
            <a 
              href={audioUrl} 
              target="_blank"
              rel="noopener noreferrer"
              style={{ 
                backgroundColor: '#FF9800', 
                color: 'white', 
                padding: '8px 16px', 
                textDecoration: 'none', 
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              🎵 Open in New Tab
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
