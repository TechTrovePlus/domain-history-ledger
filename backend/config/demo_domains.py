# backend/config/demo_domains.py

# Locked demo domains for DNS Guard V2
# These must NOT change without updating the V2 specification.

DEMO_DOMAINS = {
    "CLEAN": "clean-example.org",
    "NEW": "amazon-deals-support.net",
    "TROJAN": "trusted-blog.com",
    "ZOMBIE": "old-scam-domain.com",
}

# Convenience set for quick checks
DEMO_DOMAIN_SET = set(DEMO_DOMAINS.values())
