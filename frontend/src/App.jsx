import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

function App() {
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [scoreResult, setScoreResult] = useState(null);
  const [error, setError] = useState('');

  // JD Drop handler
  const onDropJD = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    setJdFile(file);

    if (file.type === 'text/plain') {
      const reader = new FileReader();
      reader.onload = (event) => {
        setJdText(event.target.result);
      };
      reader.readAsText(file);
    } else {
      setJdText('');
    }
  }, []);

  // Resume Drop handler
  const onDropResume = useCallback((acceptedFiles) => {
    setResumeFile(acceptedFiles[0]);
  }, []);

  const {
    getRootProps: getJDRootProps,
    getInputProps: getJDInputProps,
    isDragActive: isJDDropActive,
  } = useDropzone({ onDrop: onDropJD, accept: { 'application/pdf': [], 'text/plain': [] } });

  const {
    getRootProps: getResumeRootProps,
    getInputProps: getResumeInputProps,
    isDragActive: isResumeDropActive,
  } = useDropzone({ onDrop: onDropResume, accept: { 'application/pdf': [] } });

  const handleManualJDInput = (e) => {
    setJdText(e.target.value);
    setJdFile(null);
  };

  const handleSubmit = async () => {
    if (!jdFile && !jdText) {
      setError("Please provide a job description (upload or paste).");
      return;
    }
    if (!resumeFile) {
      setError("Please upload a resume.");
      return;
    }

    const formData = new FormData();
    formData.append('resume', resumeFile);

    if (jdFile && jdFile.type === 'application/pdf') {
      formData.append('jd_pdf', jdFile);
    } else {
      formData.append('job_description', jdText);
    }

    try {
      const response = await axios.post(
        'https://resume-ats-portal.onrender.com/api/score',
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setScoreResult(response.data);
      setError('');
    } catch (err) {
      setError("Error while processing. Please check the files or try again.");
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'Arial' }}>
      <h2>ATS Resume Scoring Tool</h2>

      <div {...getJDRootProps()} style={dropzoneStyle(isJDDropActive)}>
        <input {...getJDInputProps()} />
        <p>📄 Drag & drop Job Description here (.pdf or .txt), or click to select</p>
        {jdFile && <p><strong>Selected:</strong> {jdFile.name}</p>}
      </div>

      <div style={{ marginTop: '1rem' }}>
        <label>✍️ Or paste JD manually</label><br />
        <textarea
          placeholder="Paste job description here..."
          value={jdText}
          onChange={handleManualJDInput}
          rows={6}
          cols={60}
        />
      </div>

      <div {...getResumeRootProps()} style={dropzoneStyle(isResumeDropActive)}>
        <input {...getResumeInputProps()} />
        <p>📎 Drag & drop Resume here (PDF only), or click to select</p>
        {resumeFile && <p><strong>Selected:</strong> {resumeFile.name}</p>}
      </div>

      <button onClick={handleSubmit} style={{ marginTop: '1.5rem', padding: '0.5rem 1rem' }}>
        Get ATS Score
      </button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {scoreResult && (
        <div style={{ marginTop: '2rem', borderTop: '1px solid #ccc', paddingTop: '1rem' }}>
          <h3>✅ ATS Score: {scoreResult.ATS_Score}</h3>
          <p><strong>Strengths:</strong> {scoreResult.Strengths.join(', ')}</p>
          <p><strong>Gaps:</strong> {scoreResult.Gaps.join(', ')}</p>
          <p><strong>Recommendation:</strong> {scoreResult.Recommendation}</p>
        </div>
      )}
    </div>
  );
}

const dropzoneStyle = (isActive) => ({
  border: '2px dashed #aaa',
  borderRadius: '10px',
  padding: '1.5rem',
  textAlign: 'center',
  marginTop: '1rem',
  backgroundColor: isActive ? '#e8f5ff' : '#fafafa',
  cursor: 'pointer',
});

export default App;
