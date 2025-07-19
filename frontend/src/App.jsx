import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    setLoading(true);
    try {
      const response = await axios.post(
        'https://resume-ats-portal.onrender.com/api/score',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      setResult(response.data);
    } catch (err) {
      alert('Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>📄 Resume ATS Parser</h1>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".pdf" onChange={handleFileChange} />
        <button type="submit" disabled={!file || loading}>
          {loading ? 'Uploading...' : 'Upload Resume'}
        </button>
      </form>

      {result && (
        <div className="result">
          <h2>Parsed Result:</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
