let lastSearchedDomain = null;
let currentAbortController = null;
let currentPollTimeout = null;

function cancelSearch() {
  if (currentAbortController) currentAbortController.abort();
  if (currentPollTimeout) clearTimeout(currentPollTimeout);

  const resultDiv = document.getElementById("result");
  const searchBtn = document.getElementById("searchBtn");

  resultDiv.innerHTML = `
    <div style="text-align: center; color: var(--text-muted); padding: 20px;">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 12px; color: var(--text-muted);"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
      <div><strong style="font-size: 1.1rem;">Analysis Cancelled</strong></div>
      <div style="font-size: 0.95rem; margin-top: 8px;">The background gathering process will gracefully continue, but live updates have been terminated.</div>
    </div>
  `;

  searchBtn.disabled = false;
  searchBtn.style.opacity = "1";
}

function handleKeyPress(event) {
  if (event.key === 'Enter') {
    searchDomain();
  }
}

async function searchDomain(pollDomain = null) {
  const domainInput = document.getElementById("domainInput");
  const domain = pollDomain || domainInput.value.trim().toLowerCase();

  const resultCard = document.getElementById("result-card");
  const resultDiv = document.getElementById("result");
  const timelineBtn = document.getElementById("timelineBtn");
  const timelineContainer = document.getElementById("timeline-container");
  const searchBtn = document.getElementById("searchBtn");

  if (!domain) {
    domainInput.focus();
    return;
  }

  // Update State 
  lastSearchedDomain = domain;
  resultCard.style.display = "block";
  resultDiv.style.display = "block";
  timelineContainer.style.display = "none";
  timelineBtn.style.display = "none";

  searchBtn.disabled = true;
  searchBtn.style.opacity = "0.7";

  // Reset AbortController and Polling Timeouts
  if (currentAbortController) currentAbortController.abort();
  if (currentPollTimeout) clearTimeout(currentPollTimeout);
  currentAbortController = new AbortController();

  // Loading UI only on fresh search
  if (!pollDomain) {
    resultDiv.innerHTML = `
      <div class="loading-container">
        <div class="spinner"></div>
        <div class="loading-title">Interrogating Oracles...</div>
        <div class="loading-desc">If this is the first time we've encountered <strong>${domain}</strong>, an exhaustive background assessment is being executed across historical and abuse oracles. This may take 5-10 seconds.</div>
        <button onclick="cancelSearch()" class="btn btn-secondary" style="margin-top: 20px; width: 100%; border-color: rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); cursor: pointer;">Cancel Analysis</button>
      </div>
    `;
  }

  let isPolling = false;

  try {
    const response = await fetch(`http://localhost:5000/search?domain=${domain}`, {
      signal: currentAbortController.signal
    });
    const data = await response.json();

    if (response.status === 202) {
      isPolling = true;
      currentPollTimeout = setTimeout(() => {
        searchDomain(domain);
      }, 2500);
      return;
    }

    if (response.status !== 200) {
      resultDiv.innerHTML = `
        <div style="color: var(--untrusted); text-align: center; padding: 20px;">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 12px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 8px;">Resolution Failed</div>
          <div style="color: var(--text-muted); font-size: 0.95rem;">${data.message || data.error || data.reason || "Failed to fetch domain intelligence."}</div>
        </div>
      `;
      return;
    }

    // Determine status text & colors
    const statusClass = data.status === "TRUSTED" ? "TRUSTED" : data.status === "UNTRUSTED" ? "UNTRUSTED" : "UNKNOWN";

    // Penalties
    let penaltiesHtml = "";
    if (data.penalties && data.penalties.length > 0) {
      penaltiesHtml = `<ul class="penalty-list">`;
      data.penalties.forEach(p => {
        penaltiesHtml += `
          <li class="penalty-item">
            <span class="penalty-amount">-${p.amount}</span>
            <span class="penalty-reason">${p.reason}</span>
          </li>`;
      });
      penaltiesHtml += `</ul>`;
    }

    // Fetch Domain Intelligence Report
    let reportHtml = "";
    try {
      if (domain !== "") {
        const reportRes = await fetch(`http://localhost:5000/report/${domain}`, {
          signal: currentAbortController.signal
        });
        if (reportRes.status === 200) {
          const reportData = await reportRes.json();

          // Render Score Explanation Panel
          let explanationHtml = `<div class="card" style="margin-top: 20px; text-align: left; background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 8px;">
            <h3 style="margin-top: 0; margin-bottom: 12px; font-size: 1rem; color: var(--text-primary);">Trust Score Explanation</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
              <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <th style="text-align: left; padding: 8px 4px; color: var(--text-muted);">Factor</th>
                <th style="text-align: right; padding: 8px 4px; color: var(--text-muted);">Impact</th>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Base Score</td>
                <td style="text-align: right; padding: 8px 4px; color: var(--trusted);">+${reportData.score_breakdown.base_score || 100}</td>
              </tr>`;

          if (reportData.score_breakdown.penalties && reportData.score_breakdown.penalties.length > 0) {
            reportData.score_breakdown.penalties.forEach(p => {
              let impactVal = p.penalty || p.amount || 0;
              let impactStr = impactVal > 0 ? `&minus;${impactVal}` : `+${Math.abs(impactVal)}`;
              let color = impactVal > 0 ? "var(--untrusted)" : "var(--trusted)";
              let label = p.type || p.reason || "Unknown";

              // Friendly re-mapping of known backend constants
              const niceLabels = {
                "ABUSE_HISTORY_DETECTED": "Abuse History",
                "ACTIVE_THREAT_DETECTED": "Active Threat",
                "HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION": "Discontinuity",
                "RE_REGISTRATION": "Re-Registration",
                "DOMAIN_DROPPED": "Domain Dropped",
                "REGISTRAR_TRANSFER": "Registrar Transfer"
              };
              label = niceLabels[label] || label;

              explanationHtml += `
               <tr>
                 <td style="padding: 8px 4px; color: ${color};">${label}</td>
                 <td style="text-align: right; padding: 8px 4px; color: ${color};">${impactStr}</td>
               </tr>`;
            });
          }
          explanationHtml += `</table></div>`;

          // Render Intelligence Checks Panel
          const ic = reportData.intelligence_checks || {};

          let domainAgeStr = "Unknown";
          if (ic.domain_age_years !== undefined && ic.domain_age_years !== null && ic.domain_age_years > 0) {
            domainAgeStr = `${ic.domain_age_years} years`;
          }

          let abuseStatus = ic.abuse_history_detected === undefined ? "Unknown" : (ic.abuse_history_detected ? "Detected" : "Clean");
          let abuseColor = ic.abuse_history_detected === undefined ? "var(--unknown)" : (ic.abuse_history_detected ? "var(--untrusted)" : "var(--trusted)");

          let discStatus = ic.historical_discontinuity === undefined ? "Unknown" : (ic.historical_discontinuity ? "Yes" : "No");
          let discColor = ic.historical_discontinuity === undefined ? "var(--unknown)" : (ic.historical_discontinuity ? "var(--untrusted)" : "var(--text-muted)");

          let instabStatus = ic.lifecycle_instability === undefined ? "Unknown" : (ic.lifecycle_instability ? "Yes" : "No");
          let instabColor = ic.lifecycle_instability === undefined ? "var(--unknown)" : (ic.lifecycle_instability ? "var(--untrusted)" : "var(--text-muted)");

          let checksHtml = `<div class="card" style="margin-top: 15px; text-align: left; background: var(--card-bg); border: 1px solid var(--border-color); padding: 15px; border-radius: 8px;">
            <h3 style="margin-top: 0; margin-bottom: 12px; font-size: 1rem; color: var(--text-primary);">Domain Intelligence Report</h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
              <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                <th style="text-align: left; padding: 8px 4px; color: var(--text-muted);">Check</th>
                <th style="text-align: right; padding: 8px 4px; color: var(--text-muted);">Result</th>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Domain Exists</td>
                <td style="text-align: right; padding: 8px 4px; color: var(--trusted);">Yes</td>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Domain Age</td>
                <td style="text-align: right; padding: 8px 4px; color: var(--text-muted);">${domainAgeStr}</td>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Abuse History</td>
                <td style="text-align: right; padding: 8px 4px; color: ${abuseColor};">${abuseStatus}</td>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Historical Discontinuity</td>
                <td style="text-align: right; padding: 8px 4px; color: ${discColor};">${discStatus}</td>
              </tr>
              <tr>
                <td style="padding: 8px 4px;">Lifecycle Instability</td>
                <td style="text-align: right; padding: 8px 4px; color: ${instabColor};">${instabStatus}</td>
              </tr>
            </table>
          </div>`;

          reportHtml = explanationHtml + checksHtml;
        }
      }
    } catch (e) {
      console.warn("Could not fetch intelligence report", e);
    }

    // Success UI Rendering
    resultDiv.innerHTML = `
      <div class="status-badge ${statusClass}">
        <span style="margin-right: 6px;">●</span> ${data.status}
      </div>
      
      <div style="margin-bottom: 4px; color: var(--text-muted); font-size: 0.95rem;">DNS Guard Trust Score</div>
      <div class="trust-score-container" style="flex-wrap: wrap;">
        <div class="trust-score">${data.final_score}</div>
        <div class="trust-score-max">/ 100</div>
        <div class="score-gauge">
            <div id="scoreBar"></div>
        </div>
      </div>
      
      ${reportHtml}

      ${penaltiesHtml}
      
      <div class="stats-footer" style="margin-top: 20px;">
        <div>Target: <strong>${data.domain}</strong></div>
        <div><strong>${data.event_count}</strong> Ledger Events (${data.anchored_proofs} Validated On-Chain)</div>
      </div>
    `;

    setTimeout(() => {
      const scoreBar = document.getElementById("scoreBar");
      if (scoreBar) {
        scoreBar.style.width = data.final_score + "%";

        if (data.final_score >= 70) {
          scoreBar.style.background = "#3fb950";  // green
        }
        else if (data.final_score >= 40) {
          scoreBar.style.background = "#d29922";  // orange
        }
        else {
          scoreBar.style.background = "#ff7b72";  // red
        }
      }
    }, 10);

    // Only show timeline button if we have actual events
    if (data.event_count && data.event_count > 0) {
      timelineBtn.style.display = "flex";
    }

    // Fetch Monitoring Status
    try {
      if (domain !== "") {
        const monitorRes = await fetch(`http://localhost:5000/monitor/${domain}`, {
          signal: currentAbortController.signal
        });
        if (monitorRes.status === 200) {
          const monitorData = await monitorRes.json();
          document.getElementById("monitoringPanel").style.display = "block";
          updateMonitoringUI(monitorData);
        }
      }
    } catch (e) {
      console.warn("Could not fetch monitoring status", e);
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('Search intentionally aborted by user.');
      return;
    }
    resultDiv.innerHTML = `
      <div style="text-align: center; color: var(--untrusted); padding: 20px;">
        <div><strong>Network Error</strong></div>
        <div style="font-size: 0.9rem; margin-top: 8px; color: var(--text-muted);">Cannot reach the DNS Guard intelligence backend at localhost:5000. Ensure the Python API is running.</div>
      </div>
    `;
    console.error(err);
  } finally {
    if (!isPolling) {
      searchBtn.disabled = false;
      searchBtn.style.opacity = "1";
    }
  }
}

function updateMonitoringUI(data) {
  const status = document.getElementById("monitoringStatus");
  const btn = document.getElementById("monitorToggleBtn");

  if (data.monitored) {
    status.innerHTML = "Status: <strong style='color:#3fb950'>Enabled</strong>";
    btn.innerText = "Disable Monitoring";
  } else {
    status.innerHTML = "Status: <strong style='color:#ff7b72'>Disabled</strong>";
    btn.innerText = "Enable Monitoring";
  }
}

async function toggleMonitoring() {
  if (!lastSearchedDomain) return;

  try {
    const response = await fetch(`http://localhost:5000/monitor/${lastSearchedDomain}`, {
      method: 'POST'
    });

    if (response.status === 200) {
      const data = await response.json();
      updateMonitoringUI(data);
    } else {
      console.error("Failed to toggle monitoring status.");
    }
  } catch (e) {
    console.error("Network error while linking monitoring toggle:", e);
  }
}

async function loadTimeline() {
  const timelineContainer = document.getElementById("timeline-container");
  const timelineDiv = document.getElementById("timeline");
  const timelineMeta = document.getElementById("timeline-meta");
  const timelineBtn = document.getElementById("timelineBtn");

  if (!lastSearchedDomain) return;

  timelineBtn.style.display = "none";
  timelineContainer.style.display = "block";
  timelineMeta.innerHTML = "Querying ledger...";

  timelineDiv.innerHTML = `
    <div class="loading-container" style="padding: 40px 0;">
      <div class="spinner"></div>
      <div class="loading-title">Decrypting Ledger Sequence</div>
    </div>
  `;

  try {
    const response = await fetch(`http://localhost:5000/timeline?domain=${lastSearchedDomain}`);
    const data = await response.json();

    if (!data.events || data.events.length === 0) {
      timelineDiv.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 20px;">No discrete lifecycle events found in the encrypted volume.</div>`;
      timelineMeta.innerHTML = "0 Events";
      return;
    }

    timelineMeta.innerHTML = `${data.total_events} Entries Total`;
    timelineDiv.innerHTML = ""; // Clear loader

    data.events.forEach(event => {
      // Blockchain Proof Block
      let proofHtml = `
        <div class="blockchain-proof proof-queued">
          <div class="proof-icon">⏳</div>
          <div class="proof-details">
            <strong style="display: block; margin-bottom: 2px;">Queued for On-Chain Anchoring</strong>
            <span style="font-size: 0.8rem;">Waiting for local node validator pickup</span>
          </div>
        </div>
      `;

      if (event.blockchain_proof) {
        let niceEventType = event.event_type;
        if (niceEventType.length > 25) {
          niceEventType = niceEventType.substring(0, 22) + "...";
        }

        proofHtml = `
          <div class="blockchain-proof" style="display: block;">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
               <div class="proof-icon" style="margin-right: 8px;">⛓️</div>
               <strong style="color: #3fb950;">Blockchain Proof</strong>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 5px;">
              <tr style="border-bottom: 1px solid rgba(46, 160, 67, 0.2);">
                <th style="text-align: left; padding: 4px; color: var(--text-muted);">Event</th>
                <th style="text-align: left; padding: 4px; color: var(--text-muted);">Block</th>
                <th style="text-align: left; padding: 4px; color: var(--text-muted);">Transaction</th>
              </tr>
              <tr>
                <td style="padding: 4px; color: var(--text-main); font-family: monospace;" title="${event.event_type}">${niceEventType}</td>
                <td style="padding: 4px; color: var(--text-main);">${event.blockchain_proof.block_number}</td>
                <td style="padding: 4px;">
                    <a class="proof-tx" href="http://localhost:8545/tx/${event.blockchain_proof.transaction_hash}" target="_blank">${event.blockchain_proof.transaction_hash.substring(0, 10)}...</a>
                </td>
              </tr>
            </table>
          </div>
        `;
      }

      // Metadata JSON formatting
      let metadataMarkup = '';
      if (Object.keys(event.metadata).length > 0) {
        metadataMarkup = `<pre class="event-metadata">${JSON.stringify(event.metadata, null, 2)}</pre>`;
      }

      const formattedDate = event.date ? new Date(event.date).toLocaleString([], { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown Date';

      // Determine colors based on event type
      let typeColor = '#58a6ff'; // Default blue
      if (event.event_type.includes('ABUSE') || event.event_type.includes('THREAT') || event.event_type.includes('DROP')) typeColor = '#ff7b72'; // Red
      if (event.event_type === 'INITIAL_BACKGROUND_ASSESSMENT' || event.event_type.includes('REGISTERED')) typeColor = '#3fb950'; // Green
      if (event.event_type.includes('TRANSFER')) typeColor = '#d29922'; // Orange

      timelineDiv.innerHTML += `
        <div class="event-wrapper" style="--primary: ${typeColor}">
          <div class="event-marker"></div>
          <div class="event-header">
            <div class="event-type" style="color: ${typeColor}">${event.event_type}</div>
            <div class="event-date">${formattedDate}</div>
          </div>
          
          <div class="event-hash" title="Cryptographic Event Identity">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px; vertical-align: -1px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            ${event.event_hash}
          </div>
          
          ${metadataMarkup}
          ${proofHtml}
        </div>
      `;
    });

  } catch (err) {
    timelineDiv.innerHTML = `
      <div style="text-align: center; color: var(--untrusted); padding: 20px;">
        <div><strong>Ledger Decryption Error</strong></div>
        <div style="font-size: 0.9rem; margin-top: 8px; color: var(--text-muted);">Failed to query timeline API.</div>
      </div>
    `;
    timelineMeta.innerHTML = "Error";
    console.error(err);
  }
}
