from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.api.search import search_domain
from backend.api.timeline import get_domain_timeline
from backend.api.verify import verify_blueprint
from backend.api.monitor import monitor_blueprint
from backend.api.report import report_blueprint

app = Flask(__name__)
CORS(app)

app.register_blueprint(verify_blueprint)
app.register_blueprint(monitor_blueprint)
app.register_blueprint(report_blueprint)


@app.route("/search")
def search():
    domain = request.args.get("domain")

    if not domain:
        return jsonify({"error": "domain parameter is required"}), 400

    result = search_domain(domain)
    
    http_status = 200
    if result.get("status") == "SCAN_QUEUED":
        http_status = 202
    elif result.get("status") == 500:
        http_status = 500
        
    return jsonify(result), http_status


@app.route("/timeline")
def timeline():
    domain = request.args.get("domain")

    if not domain:
        return jsonify({"error": "domain parameter is required"}), 400

    result = get_domain_timeline(domain)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

