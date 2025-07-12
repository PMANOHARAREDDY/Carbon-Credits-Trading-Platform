import React, { useEffect, useState, useRef } from 'react';

function Onboarding({ userEmail, setRefresh, refresh }) {
  const [projects, setProjects] = useState([]);
  const [credits, setCredits] = useState([]);
  const [selectedPosition, setSelectedPosition] = useState(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  // Fetch all projects owned by the user and all credits currently owned by the user
  const fetchProjectsAndCredits = () => {
    fetch('http://localhost:5000/projects')
      .then(res => res.json())
      .then(data => setProjects(data.filter(p => p.owner_email === userEmail)));
    fetch('http://localhost:5000/board/creditwise_history')
      .then(res => res.json())
      .then(data => setCredits(data.filter(c => c.owner_email === userEmail)));
  };

  useEffect(() => {
    fetchProjectsAndCredits();
  }, [refresh]);

  useEffect(() => {
    if (window.google && mapRef.current && !mapRef.current.map) {
      const map = new window.google.maps.Map(mapRef.current, {
        center: { lat: 20.5937, lng: 78.9629 }, // Default center (India)
        zoom: 5,
      });
      mapRef.current.map = map;

      const marker = new window.google.maps.Marker({
        position: null,
        map: map,
        draggable: true,
      });
      markerRef.current = marker;

      map.addListener('click', (e) => {
        const latLng = e.latLng;
        marker.setPosition(latLng);
        setSelectedPosition({ lat: latLng.lat(), lng: latLng.lng() });
      });

      marker.addListener('dragend', () => {
        const pos = marker.getPosition();
        setSelectedPosition({ lat: pos.lat(), lng: pos.lng() });
      });
    }
  }, []);

  const handleRegister = (e) => {
    e.preventDefault();
    const name = e.target.elements.projectName.value;
    if (!selectedPosition) {
      alert('Please select a position on the map.');
      return;
    }
    fetch('http://localhost:5000/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        user_email: userEmail,
        latitude: selectedPosition.lat,
        longitude: selectedPosition.lng,
      }),
    })
      .then(res => res.json())
      .then(data => {
        alert('Project registered! Project ID: ' + data.project_id);
        setRefresh(r => r + 1);
        fetchProjectsAndCredits();
        setSelectedPosition(null);
        if (markerRef.current) {
          markerRef.current.setPosition(null);
        }
      });
  };

  const handleIssueCredit = (projectId) => {
    fetch('http://localhost:5000/issue_credit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, amount: 10, owner_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'issued') {
          alert('Credit issued! Awaiting board verification.');
          setRefresh(r => r + 1);
          fetchProjectsAndCredits();
        } else {
          alert(data.message || 'Credit issuance failed');
        }
      });
  };

  const handleSell = (creditId) => {
    fetch('http://localhost:5000/set_for_sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: creditId, user_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Credit put up for sale!');
          setRefresh(r => r + 1);
          fetchProjectsAndCredits();
        } else {
          alert(data.message || 'Failed to put credit for sale');
        }
      });
  };

  const handleRemoveFromSale = (creditId) => {
    fetch('http://localhost:5000/remove_from_sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: creditId, user_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Credit removed from sale!');
          setRefresh(r => r + 1);
          fetchProjectsAndCredits();
        } else {
          alert(data.message || 'Failed to remove credit from sale');
        }
      });
  };

  return (
    <div className="section">
      <form onSubmit={handleRegister}>
        <h2>Project Registration</h2>
        <input name="projectName" placeholder="Project Name" required />
        <div
          ref={mapRef}
          style={{ width: '100%', height: '300px', marginTop: '10px', marginBottom: '10px' }}
        />
        <button type="submit">Register</button>
      </form>
      <h3>Your Projects</h3>
      <ul>
        {projects.map(project => (
          <li key={project.project_id} className="credit-info">
            {project.name} (ID: {project.project_id}) - Status: {project.status}
            {project.status === 'verified' && (
              <button
                onClick={() => handleIssueCredit(project.project_id)}
                className="button-margin-left"
              >
                Issue Credit
              </button>
            )}
            <ul>
              {credits.filter(c => c.project_id === project.project_id).length === 0 && (
                <li className="italic-gray">No credits currently owned for this project.</li>
              )}
              {credits.filter(c => c.project_id === project.project_id).map(credit => (
                <li key={credit.credit_id} className="credit-info">
                  Credit ID: {credit.credit_id}, Status: {credit.status}, For Sale: {credit.for_sale ? 'Yes' : 'No'}, Blocked: {credit.blocked ? 'Yes' : 'No'}
                  {credit.status === 'verified' && !credit.for_sale && !credit.blocked && (
                    <button onClick={() => handleSell(credit.credit_id)} className="button-margin-left">
                      Sell
                    </button>
                  )}
                  {credit.for_sale && !credit.blocked && (
                    <button onClick={() => handleRemoveFromSale(credit.credit_id)} className="button-margin-left">
                      Remove from Sale
                    </button>
                  )}
                  {credit.blocked && (
                    <span className="status-red button-margin-left">Blocked by Board</span>
                  )}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Onboarding;
