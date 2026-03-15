from flask import Blueprint, jsonify
from backend.db import get_db_cursor
import logging

logger = logging.getLogger(__name__)

monitor_blueprint = Blueprint('monitor', __name__)

@monitor_blueprint.route('/monitor/<domain>', methods=['GET'])
def check_monitor(domain):
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT monitored FROM domains WHERE domain_name = %s", (domain,))
            domain_record = cursor.fetchone()
            
            if not domain_record:
                return jsonify({
                    "monitoring_enabled": False,
                    "status": "not_configured"
                }), 200
                
            return jsonify({
                "domain": domain,
                "monitored": domain_record['monitored']
            }), 200
    except Exception as e:
        logger.exception(f"Error evaluating monitor status for {domain}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@monitor_blueprint.route('/monitor/<domain>', methods=['POST'])
def toggle_monitor(domain):
    try:
        with get_db_cursor(commit=True) as cursor:
            # Check if domain exists
            cursor.execute("SELECT id, monitored FROM domains WHERE domain_name = %s", (domain,))
            domain_record = cursor.fetchone()
            
            if not domain_record:
                return jsonify({"error": "Domain not found"}), 404

            # Flip the boolean
            new_monitored_state = not domain_record['monitored']
            
            cursor.execute(
                "UPDATE domains SET monitored = %s WHERE id = %s",
                (new_monitored_state, domain_record['id'])
            )

            logger.info(f"[{domain}] Monitoring toggled to {new_monitored_state}")
            return jsonify({
                "domain": domain,
                "monitored": new_monitored_state
            }), 200

    except Exception as e:
        logger.exception(f"Error toggling monitor for {domain}: {e}")
        return jsonify({"error": "Internal server error toggling monitor"}), 500
