let lastSearchedDomain = null;

async function searchDomain() {
  const domain = document.getElementById("domainInput").value;
  const resultDiv = document.getElementById("result");
  const timelineDiv = document.getElementById("timeline");

  if (!domain) {
    resultDiv.innerHTML = "Please enter a domain.";
    return;
  }

  lastSearchedDomain = domain;
  resultDiv.innerHTML = "Searching...";
  timelineDiv.innerHTML = "";

  try {
    const response = await fetch(
      `http://localhost:5000/search?domain=${domain}`
    );
    const data = await response.json();

    resultDiv.className = `result ${data.status}`;

    resultDiv.innerHTML = `
      <div><span class="label">Status:</span> ${data.status}</div>
      <div><span class="label">Reason:</span> ${data.reason}</div>
    `;

    if (data.blockchain_proof) {
      resultDiv.innerHTML += `
        <div class="proof">
          <span class="label">Blockchain Proof:</span><br/>
          Hash: ${data.blockchain_proof.integrity_hash}<br/>
          Tx: ${data.blockchain_proof.transaction}
        </div>
      `;
    }

  } catch (err) {
    resultDiv.innerHTML = "Error contacting backend.";
  }
}

async function loadTimeline() {
  const timelineDiv = document.getElementById("timeline");

  if (!lastSearchedDomain) {
    timelineDiv.innerHTML = "Search for a domain first.";
    return;
  }

  timelineDiv.innerHTML = "Loading timeline...";

  try {
    const response = await fetch(
      `http://localhost:5000/timeline?domain=${lastSearchedDomain}`
    );
    const data = await response.json();

    if (!data.events || data.events.length === 0) {
      timelineDiv.innerHTML = "No timeline data available.";
      return;
    }

    timelineDiv.innerHTML = "<h3>Domain Timeline</h3>";

    data.events.forEach(event => {
      let proofHtml = "";

      if (event.blockchain_proof) {
        proofHtml = `
          <div class="proof">
            <strong>Blockchain Proof</strong><br/>
            Hash: ${event.blockchain_proof.integrity_hash}<br/>
            Tx: ${event.blockchain_proof.transaction}
          </div>
        `;
      }

      timelineDiv.innerHTML += `
        <div class="timeline-event ${event.event_type}">
          <div class="event-date">${event.date}</div>
          <div><strong>${event.event_type}</strong></div>
          <div>${event.description}</div>
          ${proofHtml}
        </div>
      `;
    });

  } catch (err) {
    timelineDiv.innerHTML = "Error loading timeline.";
  }
}
