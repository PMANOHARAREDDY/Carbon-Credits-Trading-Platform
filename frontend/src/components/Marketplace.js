import React, { useEffect, useState } from 'react';

function Marketplace({ userEmail, refresh }) {
  const [ownedCredits, setOwnedCredits] = useState([]);
  const [marketCredits, setMarketCredits] = useState([]);

  const fetchOwnedCredits = () => {
    fetch('http://localhost:5000/list_credits?user_email=' + userEmail)
      .then(res => res.json())
      .then(data => setOwnedCredits(data));
  };

  const fetchMarketCredits = () => {
    fetch('http://localhost:5000/list_credits?user_email=' + userEmail + '&market=true')
      .then(res => res.json())
      .then(data => setMarketCredits(data));
  };

  useEffect(() => {
    fetchOwnedCredits();
    fetchMarketCredits();
  }, [refresh]);

  const handleBuy = (credit) => {
    if (credit.owner_email === userEmail) {
      alert('You already own this credit.');
      return;
    }
    fetch('http://localhost:5000/purchase_credit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: credit.credit_id, buyer_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Purchase successful!');
          fetchOwnedCredits();
          fetchMarketCredits();
        } else {
          alert(data.message || 'Purchase failed');
        }
      });
  };

  const handleSetForSale = (credit) => {
    fetch('http://localhost:5000/set_for_sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: credit.credit_id, user_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Credit put for sale successfully!');
          fetchOwnedCredits();
          fetchMarketCredits();
        } else {
          alert(data.message || 'Failed to put credit for sale');
        }
      });
  };

  const handleRemoveFromSale = (credit) => {
    fetch('http://localhost:5000/remove_from_sale', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credit_id: credit.credit_id, user_email: userEmail })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          alert('Credit removed from sale successfully!');
          fetchOwnedCredits();
          fetchMarketCredits();
        } else {
          alert(data.message || 'Failed to remove credit from sale');
        }
      });
  };

  return (
    <div className="section">
      <h2>Credits on Market</h2>
      <button onClick={() => { fetchOwnedCredits(); fetchMarketCredits(); }}>Refresh</button>
      {ownedCredits.length === 0 && <p>No owned credits found.</p>}
      {ownedCredits.map(credit => (
        <div key={credit.credit_id} className="card credit-info">
          <p>Credit ID: {credit.credit_id}, Project ID: {credit.project_id}, Amount: {credit.amount}, Issuer: {credit.issuer_email}, Owner: {credit.owner_email}, Status: {credit.status}</p>
          {!credit.for_sale && (
            <button onClick={() => handleSetForSale(credit)} className="button-margin-left">
              Put for Sale
            </button>
          )}
          {credit.for_sale && (
            <button onClick={() => handleRemoveFromSale(credit)} className="button-margin-left">
              Remove from Sale
            </button>
          )}
        </div>
      ))}

      <h2>Credits for Sale</h2>
      {marketCredits.length === 0 && <p>No credits for sale found.</p>}
      {marketCredits.map(credit => (
        <div key={credit.credit_id} className="card credit-info">
          <p>Credit ID: {credit.credit_id}, Project ID: {credit.project_id}, Amount: {credit.amount}, Issuer: {credit.issuer_email}, Owner: {credit.owner_email}, Status: {credit.status}</p>
          {credit.owner_email !== userEmail && (
            <button onClick={() => handleBuy(credit)} className="button-margin-left">
              Buy
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

export default Marketplace;
