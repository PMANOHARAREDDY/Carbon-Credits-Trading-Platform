import React, { useEffect, useState } from 'react';

function BoardVerify({ userEmail, setRefresh, refresh }) {
  const [projectwise, setProjectwise] = useState([]);
  const [credits, setCredits] = useState([]);

  const fetchData = () => {
    fetch('http://localhost:5000/board/projectwise_credits')
      .then(res => res.json())
      .then(data => setProjectwise(data));
    fetch('http://localhost:5000/board/creditwise_history')
      .then(res => res.json())
      .then(data => setCredits(data));
  };

  useEffect(() => {
    fetchData();
  }, [refresh]);

  const handleVerifyProject = (projectId) => {
    fetch('http://localhost:5000/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, verifier_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'verified') {
          alert('Project verified!');
          setRefresh(r => r + 1);
        } else {
          alert(data.message || 'Verification failed');
        }
      });
  };

  const handleVerifyCredit = (creditId) => {
    fetch('http://localhost:5000/verify_credit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: creditId, verifier_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'verified') {
          alert('Credit verified!');
          setRefresh(r => r + 1);
        } else {
          alert(data.message || 'Credit verification failed');
        }
      });
  };

  const handleBlockCredit = (creditId) => {
    fetch('http://localhost:5000/block_credit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: creditId, board_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'blocked') {
          alert('Credit blocked!');
          setRefresh(r => r + 1);
        } else {
          alert(data.message || 'Block failed');
        }
      });
  };

  const handleReleaseCredit = (creditId) => {
    fetch('http://localhost:5000/release_credit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: creditId, board_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'released') {
          alert('Credit released!');
          setRefresh(r => r + 1);
        } else {
          alert(data.message || 'Release failed');
        }
      });
  };

  return (
    <div>
      <h2>Projectwise Credit Tracking</h2>
      {projectwise.map(({ project, credits }) => (
        <div key={project.project_id} style={{ marginBottom: 20, border: '1px solid #ccc', padding: 10 }}>
          <strong>{project.name}</strong> (ID: {project.project_id}) - Owner: {project.owner_email} - Status: {project.status}
          <br />
          <em>Location:</em> Latitude: {project.latitude || 'N/A'}, Longitude: {project.longitude || 'N/A'}
          {project.status !== 'verified' && (
            <button onClick={() => handleVerifyProject(project.project_id)} style={{ marginLeft: '10px' }}>
              Verify Project
            </button>
          )}
          <ul>
            {credits.length === 0 && <li>No credits issued yet.</li>}
            {credits.map(credit => (
              <li key={credit.credit_id}>
                Credit ID: {credit.credit_id}, Amount: {credit.amount}, Issuer: {credit.issuer_email}, Owner: {credit.owner_email}, Status: {credit.status}, For Sale: {credit.for_sale ? 'Yes' : 'No'}, Blocked: {credit.blocked ? 'Yes' : 'No'}
                {credit.status !== 'verified' && (
                  <button onClick={() => handleVerifyCredit(credit.credit_id)} style={{ marginLeft: '10px' }}>
                    Verify Credit
                  </button>
                )}
                {!credit.blocked && (
                  <button onClick={() => handleBlockCredit(credit.credit_id)} style={{ marginLeft: '10px' }}>
                    Block
                  </button>
                )}
                {credit.blocked && (
                  <button onClick={() => handleReleaseCredit(credit.credit_id)} style={{ marginLeft: '10px' }}>
                    Release
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      ))}

      <h2>Creditwise Full History</h2>
      <ul>
        {credits.map(credit => (
          <li key={credit.credit_id}>
            <strong>Credit ID: {credit.credit_id}</strong> (Project: {credit.project_id})<br />
            Amount: {credit.amount}, Issuer: {credit.issuer_email}, Owner: {credit.owner_email}, Status: {credit.status}, For Sale: {credit.for_sale ? 'Yes' : 'No'}, Blocked: {credit.blocked ? 'Yes' : 'No'}<br />
            <em>History:</em>
            <ul>
              {credit.history.map((h, idx) => (
                <li key={idx}>
                  [{h.timestamp}] {h.action} by {h.by}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default BoardVerify;
