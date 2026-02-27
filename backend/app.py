from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.api.search import search_domain
from backend.api.timeline import get_domain_timeline

app = Flask(__name__)
CORS(app)


@app.route("/search")
def search():
    domain = request.args.get("domain")

    if not domain:
        return jsonify({"error": "domain parameter is required"}), 400

    result = search_domain(domain)
    return jsonify(result)


@app.route("/timeline")
def timeline():
    domain = request.args.get("domain")

    if not domain:
        return jsonify({"error": "domain parameter is required"}), 400

    result = get_domain_timeline(domain)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

