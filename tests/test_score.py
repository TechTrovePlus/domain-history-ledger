from backend.trust.trust_engine import TrustEngine

print(TrustEngine.calculate_score([]))
print(TrustEngine.calculate_score([{"event_type": "initial_background_assessment", "event_metadata": {}}]))
