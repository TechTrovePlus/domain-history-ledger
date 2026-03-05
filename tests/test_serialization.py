import json
from backend.trust.trust_engine import TrustEngine
from backend.api.search import search_domain
from unittest.mock import patch

def test_serialization():
    # Mock events that give exactly score 80
    events = [
        {"event_type": "initial_background_assessment", "event_metadata": {}},
        {"event_type": "re_registration", "event_metadata": {}} # -20 penalty -> score 80
    ]
    
    trust_evaluation = TrustEngine.calculate_score(events)
    print("TrustEngine raw Output:", trust_evaluation)
    
    # Mocking the api response logic manually to see what it returns
    response = {
        "domain": "test.com",
        "status": "TRUSTED" if trust_evaluation["is_trusted"] else "UNTRUSTED",
        "is_trusted": trust_evaluation["is_trusted"],
        "final_score": trust_evaluation["final_score"],
        "penalties": trust_evaluation["penalties"],
        "event_count": len(events)
    }
    
    print("API Dict Output:", response)
    print("JSON serialized:", json.dumps(response))

if __name__ == "__main__":
    test_serialization()
