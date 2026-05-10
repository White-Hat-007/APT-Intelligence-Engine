TACTIC_MAP = {
    "T1059": "Execution",
    "T1547": "Persistence",
    "T1003": "Credential Access",
    "T1021": "Lateral Movement",
    "T1041": "Exfiltration"
}

def map_to_tactics(events):
    """
    Map technique IDs to MITRE tactics.
    Accepts a list of event dictionaries.
    """
    for event in events:
        event["tactic"] = TACTIC_MAP.get(event["technique_id"], "Unknown")

    return events