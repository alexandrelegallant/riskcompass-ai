"""
RiskCompass AI — Rule-based scoring engine (fallback / core logic)
Works independently of the Claude API for demo resilience.
"""

ESSENTIAL_EIGHT = [
    "Patch Applications",
    "Patch Operating Systems",
    "Multi-Factor Authentication",
    "Restrict Admin Privileges",
    "Application Control",
    "Restrict Microsoft Office Macros",
    "User Application Hardening",
    "Regular Backups",
]

WA_POLICY_MAP = {
    "Patch Applications":               ("3.1.1 Essential Eight – Patch Applications", "Within 48 hours"),
    "Patch Operating Systems":          ("3.1.1 Essential Eight – Patch OS",            "Within 48 hours"),
    "Multi-Factor Authentication":      ("3.6 Identity and Access Management",          "Immediate (now)"),
    "Restrict Admin Privileges":        ("3.6 Identity and Access Management",          "Within 2 weeks"),
    "Application Control":              ("3.1.1 Essential Eight – App Control",          "Within 2 weeks"),
    "Restrict Microsoft Office Macros": ("3.1.1 Essential Eight – Macros",              "Within 2 weeks"),
    "User Application Hardening":       ("3.1.1 Essential Eight – App Hardening",       "Within 2 weeks"),
    "Regular Backups":                  ("3.1.2 Further Five – Backups",                "Immediate (now)"),
    "Ransomware":                       ("5.3 Ransomware Position",                     "Immediate (now)"),
    "Phishing":                         ("3.2 Cyber Security Training",                 "Within 24 hours"),
    "Supply Chain":                     ("3.4 Information Secure Procurement",          "Within 24 hours"),
    "Insider Threat":                   ("1.4 Cyber Security Governance",               "Immediate (now)"),
    "Active Exploitation":              ("4.1 Adverse Event Analysis",                  "Immediate (now)"),
    "Data Breach":                      ("5.1 Incident Management and Response Plan",   "Immediate (now)"),
    "Access Control":                   ("3.6 Identity and Access Management",          "Within 48 hours"),
    "Compliance":                       ("1.4 Cyber Security Governance",               "Within 2 weeks"),
    "Vulnerability":                    ("1.7 Vulnerability Management",                "Within 48 hours"),
}

TF_ORDER = [
    "Immediate (now)",
    "Within 24 hours",
    "Within 48 hours",
    "Within 2 weeks",
    "Scheduled",
]

def _tf_rank(t: str) -> int:
    return TF_ORDER.index(t) if t in TF_ORDER else 99


def score_alert(alert: dict) -> dict:
    """
    Score a structured alert dict and return it with priority fields added.

    Expected keys (all optional):
      cvss                 float   0–10
      internet_facing      bool
      exploit_available    bool
      active_exploitation  bool
      sensitive_data       bool
      business_criticality str    high / medium / low
      patch_available      bool
      category             str    (maps to WA_POLICY_MAP)
      essential_eight_gap  str    (maps to WA_POLICY_MAP)
    """
    score = 0.0

    # CVSS base score → 0–40 pts
    cvss = min(10.0, max(0.0, float(alert.get("cvss", 5.0))))
    score += (cvss / 10.0) * 40

    # Active exploitation → maximum urgency boost
    if alert.get("active_exploitation"):
        score += 20
    elif alert.get("exploit_available"):
        score += 12

    # Internet-facing exposure
    if alert.get("internet_facing"):
        score += 15

    # Sensitive data at risk
    if alert.get("sensitive_data"):
        score += 10

    # Business criticality
    crit = str(alert.get("business_criticality", "medium")).lower()
    score += {"high": 10, "medium": 5, "low": 2}.get(crit, 5)

    # No patch available → harder to remediate
    if not alert.get("patch_available", True):
        score += 5

    score = min(100, round(score))

    # Priority band
    if score >= 80:
        priority, base_tf = "CRITICAL", "Immediate (now)"
    elif score >= 60:
        priority, base_tf = "HIGH",     "Within 24 hours"
    elif score >= 40:
        priority, base_tf = "MEDIUM",   "Within 48 hours"
    else:
        priority, base_tf = "LOW",      "Within 2 weeks"

    # WA Policy mapping — prefer E8 gap label, fall back to category
    e8_gap   = alert.get("essential_eight_gap", "")
    category = alert.get("category", "")
    policy_key = e8_gap if e8_gap in WA_POLICY_MAP else (category if category in WA_POLICY_MAP else None)
    wa_policy, policy_tf = WA_POLICY_MAP.get(policy_key, ("2.2 Cyber Security Risk Management", base_tf)) \
        if policy_key else ("2.2 Cyber Security Risk Management", base_tf)

    # Use whichever timeframe is more urgent
    final_tf = policy_tf if _tf_rank(policy_tf) < _tf_rank(base_tf) else base_tf

    # DGov escalation flag
    escalate = (
        priority == "CRITICAL"
        or bool(alert.get("active_exploitation"))
        or category in ("Ransomware", "Active Exploitation", "Data Breach", "Insider Threat")
    )

    return {
        **alert,
        "priority_score":    score,
        "priority":          priority,
        "timeframe":         final_tf,
        "wa_policy_reference": wa_policy,
        "escalate_to_dgov":  escalate,
    }


def score_batch(alerts: list[dict]) -> list[dict]:
    """Score a list of alert dicts and return them sorted by priority_score descending."""
    scored = [score_alert(a) for a in alerts]
    return sorted(scored, key=lambda x: -x["priority_score"])
