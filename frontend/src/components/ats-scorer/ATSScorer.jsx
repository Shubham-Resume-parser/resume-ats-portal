import React, { useState } from 'react';

const ATSScorer = () => {
  const [resume, setResume] = useState(null);
  const [jobDesc, setJobDesc] = useState("");
  const [result, setResult] = useState(null);

  const handleScore = async () => {
    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("job_description", jobDesc);

    const response = await fetch("http://localhost:8000/score", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    setResult(data);
  };

  return (
    <div>
      <h2>ATS Scorer</h2>
      <input type="file" onChange={(e) => setResume(e.target.files[0])} />
      <textarea placeholder="Paste Job Description" onChange={(e) => setJobDesc(e.target.value)} />
      <button onClick={handleScore}>Get Score</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
};

export default ATSScorer;