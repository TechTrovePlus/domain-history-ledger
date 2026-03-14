from flask import Blueprint, jsonify
from backend.db import get_db_cursor
from backend.trust.trust_engine import TrustEngine
import logging
from datetime import datetime, timezone
import json
import requests

logger = logging.getLogger(__name__)

report_blueprint = Blueprint('report', __name__)

@report_blueprint.route('/report/<domain>', methods=['GET'])
def get_domain_report(domain):
    try:
        with get_db_cursor() as cursor:
            # 1. Fetch domain_id
            cursor.execute("SELECT id FROM domains WHERE domain_name = %s", (domain,))
            domain_record = cursor.fetchone()
            
            if not domain_record:
                return jsonify({"error": "Domain not found in ledger"}), 404
            
            domain_id = domain_record['id']

            # 2. Fetch all events chronologically & Check Blockchain Anchoring
            cursor.execute("""
                SELECT e.id, e.event_type, e.event_metadata, e.event_timestamp,
                       b.tx_hash, b.block_number
                FROM domain_events e
                LEFT JOIN blockchain_records b ON e.id = b.event_id
                WHERE e.domain_id = %s
                ORDER BY e.event_timestamp ASC
            """, (domain_id,))
            
            raw_events = cursor.fetchall()

            if not raw_events:
                 return jsonify({"error": "No events found for domain"}), 404

            # Prepare data structures
            events_for_trust = []
            anchored_count = 0
            
            intelligence_checks = {
                "abuse_history_detected": False,
                "historical_discontinuity": False,
                "lifecycle_instability": False,
                "domain_age_years": None
            }

            intelligence_sources = {
                "domain_exists": "RDAP",
                "domain_age": "RDAP",
                "abuse_history": "URLhaus",
                "historical_discontinuity": "Wayback",
                "lifecycle_instability": "Diff Engine"
            }

            oracle_status = {
                "rdap": "online",
                "wayback": "online",
                "urlhaus": "online"
            }

            abuse_details = None
            has_rdap_baseline = False

            for row in raw_events:
                # Reconstruct event dictionary for TrustEngine
                meta = row['event_metadata']
                if isinstance(meta, str):
                    meta = json.loads(meta)
                
                event_obj = {
                    "type": row['event_type'],
                    "metadata": meta,
                    "timestamp": row['event_timestamp']
                }
                events_for_trust.append(event_obj)

                # 4. Count blockchain anchored events
                if row['tx_hash'] and row['block_number']:
                    anchored_count += 1

                # 5. Extract intelligence signals
                if row['event_type'] == "ABUSE_HISTORY_DETECTED":
                    intelligence_checks["abuse_history_detected"] = True
                    abuse_details = {
                        "malware_types": meta.get("malware_types", []),
                        "first_seen": meta.get("first_seen", "Unknown"),
                        "url_count": meta.get("url_count", 0),
                        "online_count": meta.get("online_count", 0),
                        "offline_count": meta.get("offline_count", 0),
                        "source": "URLhaus"
                    }
                
                if row['event_type'] == "HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION":
                    intelligence_checks["historical_discontinuity"] = True

                if row['event_type'] == "RE_REGISTRATION":
                    intelligence_checks["lifecycle_instability"] = True
                
                # 6. Determine domain age from INITIAL_BACKGROUND_ASSESSMENT
                if row['event_type'] == "INITIAL_BACKGROUND_ASSESSMENT":
                    has_rdap_baseline = True
                    creation_date_str = meta.get("rdap_baseline", {}).get("creation_date")
                    if creation_date_str:
                        try:
                            # Try parsing the ISO-ish date strings commonly returned by RDAP
                            creation_date = datetime.fromisoformat(creation_date_str.replace("Z", "+00:00"))
                            age_days = (datetime.now(timezone.utc) - creation_date).days
                            intelligence_checks["domain_age_years"] = age_days // 365
                        except Exception as e:
                            logger.warning(f"Failed to parse creation_date {creation_date_str} for {domain}: {e}")
                            intelligence_checks["domain_age_years"] = None

            # Oracle Status Tracking
            if not has_rdap_baseline:
                oracle_status["rdap"] = "error"
            else:
                with get_db_cursor() as cur:
                    cur.execute("SELECT retrieved_at FROM domain_snapshots WHERE domain_id = %s ORDER BY retrieved_at DESC LIMIT 1", (domain_id,))
                    snap = cur.fetchone()
                    if snap and snap.get('retrieved_at'):
                        age = (datetime.now(timezone.utc) - snap['retrieved_at']).total_seconds() / 3600
                        if age < 24:
                            oracle_status["rdap"] = "cached"

            try:
                wb_res = requests.get("https://web.archive.org/cdx/search/cdx", params={"url": domain, "limit": 1}, timeout=3)
                if wb_res.status_code == 200:
                    oracle_status["wayback"] = "online"
                else:
                    oracle_status["wayback"] = "error"
            except requests.exceptions.Timeout:
                oracle_status["wayback"] = "timeout"
            except Exception:
                oracle_status["wayback"] = "error"

            try:
                uh_res = requests.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": domain}, timeout=10)
                if uh_res.status_code == 200:
                    if "query_status" in uh_res.json():
                        oracle_status["urlhaus"] = "online"
                    else:
                        oracle_status["urlhaus"] = "error"
                else:
                    oracle_status["urlhaus"] = "error"
            except requests.exceptions.Timeout:
                oracle_status["urlhaus"] = "timeout"
            except Exception:
                oracle_status["urlhaus"] = "error"

            if oracle_status["urlhaus"] != "online" and abuse_details is not None:
                oracle_status["urlhaus"] = "cached"

            # 3. Trust Score Calculation
            trust_result = TrustEngine.calculate_score(events_for_trust)

            # 7. Structured Response
            return jsonify({
                "domain": domain,
                "trust_summary": {
                    "status": "TRUSTED" if trust_result.get("is_trusted", False) else "UNTRUSTED",
                    "final_score": trust_result["final_score"]
                },
                "score_breakdown": {
                    "base_score": 100,
                    "penalties": trust_result["penalties"]
                },
                "intelligence_checks": intelligence_checks,
                "intelligence_sources": intelligence_sources,
                "oracle_status": oracle_status,
                "abuse_details": abuse_details,
                "ledger_summary": {
                    "total_events": len(raw_events)
                },
                "blockchain_status": {
                    "anchored_events": anchored_count,
                    "pending_anchorage": len(raw_events) - anchored_count,
                    "fully_anchored": anchored_count == len(raw_events)
                }
            }), 200

    except Exception as e:
        logger.exception(f"Error generating report for {domain}: {e}")
        return jsonify({"error": "Internal server error generating report"}), 500
