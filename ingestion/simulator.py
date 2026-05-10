import random
import uuid
from datetime import datetime, timezone

TECHNIQUES = {
    "T1059": "Command and Scripting Interpreter",
    "T1547": "Boot or Logon Autostart Execution",
    "T1003": "Credential Dumping",
    "T1021": "Remote Services",
    "T1041": "Exfiltration Over C2 Channel"
}

PHASES = [
    ["T1059"],
    ["T1547", "T1003"],
    ["T1021"],
    ["T1041"]
]


def generate_event(technique_id, campaign_id):
    """
    Generate a single synthetic telemetry event.
    """
    return {
        "campaign_id": campaign_id,
        "event_id": str(uuid.uuid4()),
        "timestamp": str(datetime.now(timezone.utc)),
        "host": f"HOST-{random.randint(1,3)}",
        "technique_id": technique_id,
        "technique_name": TECHNIQUES[technique_id]
    }


def simulate_campaign(campaign_id):
    """
    Simulate a full APT-style campaign with behavioral variability.
    """
    logs = []

    for phase in PHASES:
        # Randomly select techniques within phase
        selected = random.sample(phase, random.randint(1, len(phase)))

        for technique in selected:
            # Randomly repeat techniques for realism
            repeat_count = random.randint(1, 2)

            for _ in range(repeat_count):
                logs.append(generate_event(technique, campaign_id))

    return logs