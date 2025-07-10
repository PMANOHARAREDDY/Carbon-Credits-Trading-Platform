import React, { useEffect, useState } from 'react';

function Dashboard({ userEmail, refresh }) {
  const [projects, setProjects] = useState([]);
  const [credits, setCredits] = useState([]);

  useEffect(() => {
    fetch('http://localhost:5000/projects')
      .then(res => res.json())
      .then(setProjects);
    fetch('http://localhost:5000/board/creditwise_history')
      .then(res => res.json())
      .then(data => {
        // Find all credits ever owned by the user (issued, purchased, or currently owned)
        const everOwned = data.filter(credit =>
          credit.issuer_email === userEmail ||
          credit.history.some(h => h.action === 'purchased' && h.by === userEmail) ||
          credit.owner_email === userEmail
        );
        setCredits(everOwned);
      });
  }, [refresh]);

  const getProject = (projectId) =>
    projects.find(p => p.project_id === projectId);

  const isCurrentOwner = (credit) => credit.owner_email === userEmail;

  const getBuyer = (credit) => {
    const purchaseEvents = credit.history.filter(h => h.action === 'purchased');
    if (purchaseEvents.length > 0) {
      return purchaseEvents[purchaseEvents.length - 1].by;
    }
    return credit.owner_email;
  };

  return (
    <div className="section">
      <h2>Your Credits (Issued, Owned, or Sold)</h2>
      <ul>
        {credits.length === 0 && <li>No credits issued or owned yet.</li>}
        {credits.map(credit => {
          const project = getProject(credit.project_id);
          return (
            <li key={credit.credit_id} className="credit-info">
              <strong>Credit:</strong> ID: {credit.credit_id}, Amount: {credit.amount}, Status: {credit.status}, For Sale: {credit.for_sale ? 'Yes' : 'No'}
              <br />
              <strong>Project:</strong> {project ? `${project.name} (ID: ${project.project_id}) - Owner: ${project.owner_email} - Status: ${project.status}` : 'Project details not found'}
              <br />
              {isCurrentOwner(credit) ? (
                <span className="status-green">You currently own this credit.</span>
              ) : (
                <span className="status-blue">
                  Sold to {getBuyer(credit)}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default Dashboard;
