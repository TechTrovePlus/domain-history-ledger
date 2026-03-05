from flask import Blueprint, jsonify
from backend.db import get_db_cursor
from backend.trust.trust_engine import TrustEngine
import logging
from datetime import datetime
import json

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
                "domain_age_years": 0.0
            }

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
                
                if row['event_type'] == "HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION":
                    intelligence_checks["historical_discontinuity"] = True

                if row['event_type'] == "RE_REGISTRATION":
                    intelligence_checks["lifecycle_instability"] = True
                
                # 6. Determine domain age from INITIAL_BACKGROUND_ASSESSMENT
                if row['event_type'] == "INITIAL_BACKGROUND_ASSESSMENT":
                    creation_date_str = meta.get("creation_date")
                    if creation_date_str:
                        try:
                            # Try parsing the ISO-ish date strings commonly returned by RDAP
                            creation_date = datetime.fromisoformat(creation_date_str.replace("Z", "+00:00"))
                            now = datetime.now(creation_date.tzinfo)
                            delta = now - creation_date
                            intelligence_checks["domain_age_years"] = round(delta.days / 365.25, 2)
                        except Exception as e:
                            logger.warning(f"Failed to parse creation_date {creation_date_str} for {domain}: {e}")

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
