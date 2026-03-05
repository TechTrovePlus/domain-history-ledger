import logging
from backend.config.event_types import (
    ABUSE_FLAG,
    ACTIVE_THREAT_DETECTED,
    ABUSE_HISTORY_DETECTED,
    HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION,
    RE_REGISTRATION,
    REGISTRAR_TRANSFER,
    DOMAIN_DROPPED
)

logger = logging.getLogger(__name__)

class TrustEngine:
    """
    Computes a numerical trust score (0-100) based on historical intelligence 
    and lifecycle events documented in the ledger. 
    """

    BASE_SCORE = 100

    @staticmethod
    def calculate_score(events: list[dict]) -> dict:
        """
        Accepts a list of ledger event dictionaries.
        Returns a dict containing the final score and a list of penalties.
        """
        score = TrustEngine.BASE_SCORE
        penalties = []

        has_discontinuity = any(
            e.get("event_type") == HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION
            for e in events
        )

        has_rereg = any(
            e.get("event_type") == RE_REGISTRATION
            for e in events
        )

        has_drop = any(
            e.get("event_type") == DOMAIN_DROPPED
            for e in events
        )

        for event in events:
            evt_type = event.get("event_type")
            metadata = event.get("event_metadata", {})
            
            # Proportional Abuse Scoring
            if evt_type == ACTIVE_THREAT_DETECTED:
                penalty = 90
                reason = "critical_active_threat"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

            elif evt_type == ABUSE_FLAG:
                penalty = 70
                reason = "historical_abuse_flag"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

            elif evt_type == ABUSE_HISTORY_DETECTED:
                url_count = int(metadata.get("url_count", 0))
                online_count = int(metadata.get("online_count", 0))
                offline_count = int(metadata.get("offline_count", 0))
                domain_age_years = float(metadata.get("domain_age_years", 0))

                penalty = 40  # base historical abuse penalty

                # Active infrastructure boost
                if online_count > 0:
                    penalty += 30

                # High-volume scaling
                if url_count > 10:
                    penalty += 10

                # Lifecycle-aware mitigation
                if (
                    domain_age_years > 10
                    and not has_discontinuity
                    and not has_rereg
                    and not has_drop
                ):
                    penalty -= 15

                # Floor and cap
                penalty = max(penalty, 25)
                penalty = min(penalty, 80)

                score -= penalty

                penalties.append({
                    "type": evt_type,
                    "penalty": penalty,
                    "reason": "abuse_history_lifecycle_fusion"
                })

            # Historical Discontinuity
            elif evt_type == HISTORICAL_CONTENT_PREVIOUS_TO_CURRENT_REGISTRATION:
                penalty = 30
                reason = "content_predates_registration"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

            # Lifecycle Drops
            elif evt_type == DOMAIN_DROPPED:
                penalty = 40
                reason = "domain_registration_dropped"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

            # Re-Registrations
            elif evt_type == RE_REGISTRATION:
                penalty = 20
                reason = "domain_reregistered"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

            # Registrar Churn
            elif evt_type == REGISTRAR_TRANSFER:
                penalty = 10
                reason = "registrar_transferred"
                score -= penalty
                penalties.append({"type": evt_type, "penalty": penalty, "reason": reason})

        # Score boundaries
        if score < 0:
            score = 0
            
        return {
            "final_score": float(score) if '.' in str(score) else int(score),
            "penalties": penalties,
            "is_trusted": bool(int(score) >= 70)
        }
