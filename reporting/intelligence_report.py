def generate_report(fingerprint, cluster_label):
    risk_level = "High" if fingerprint["campaign_complexity_score"] > 10 else "Moderate"

    report = f"""
    ===== STRATEGIC THREAT INTELLIGENCE REPORT =====

    Cluster Classification: {cluster_label}
    Risk Level: {risk_level}

    Technique Distribution:
    {fingerprint['technique_frequency']}

    Affected Hosts:
    {fingerprint['affected_hosts']}

    Behavioral Complexity Score:
    {fingerprint['campaign_complexity_score']}

    Assessment:
    Campaign exhibits structured adversary behavior aligned with multi-stage intrusion patterns.
    """

    return report