from collections import Counter
import numpy as np

# Define the technique universe for fixed-length vectorization
ALL_TECHNIQUES = [
    "T1059",  # Execution
    "T1547",  # Persistence
    "T1003",  # Credential Access
    "T1021",  # Lateral Movement
    "T1041"   # Exfiltration
]


def generate_fingerprint(mapped_logs):
    """
    Generate a behavioral fingerprint from mapped MITRE logs.
    Produces:
    - Technique frequency distribution
    - Tactic sequence
    - Host spread
    - Behavioral vector for clustering/similarity
    """

    techniques = [e["technique_id"] for e in mapped_logs]
    tactics = [e["tactic"] for e in mapped_logs]
    hosts = set(e["host"] for e in mapped_logs)

    technique_freq = Counter(techniques)
    tactic_freq = Counter(tactics)

    unique_techniques = list(set(techniques))
    unique_tactics = list(set(tactics))

    # Behavioral complexity metric
    complexity_score = len(unique_techniques) * len(hosts)

    # 🔥 TRUE BEHAVIORAL VECTOR (Technique-based)
    # Each dimension represents frequency of a specific technique
    vector = np.array([
        technique_freq.get(t, 0) for t in ALL_TECHNIQUES
    ])

    fingerprint = {
        "unique_techniques": unique_techniques,
        "technique_frequency": dict(technique_freq),
        "tactic_frequency": dict(tactic_freq),
        "tactic_sequence": tactics,
        "affected_hosts": list(hosts),
        "campaign_complexity_score": complexity_score,
        "vector": vector
    }

    return fingerprint