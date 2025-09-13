import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await axios.post('http://localhost:8000/tts', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    setJobId(res.data.job_id);
  };

  const checkStatus = async () => {
    const res = await axios.get(`http://localhost:8000/tts/${jobId}`);
    setStatus(res.data.status);
    if (res.data.audio_url) setAudioUrl(res.data.audio_url);
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Document to Speech</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload</button>
      {jobId && (
        <div>
          <p>Job ID: {jobId}</p>
          <button onClick={checkStatus}>Check Status</button>
          <p>Status: {status}</p>
          {audioUrl && (
            <div>
              <audio controls src={audioUrl}></audio>
              <a href={audioUrl} download>Download Audio</a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}