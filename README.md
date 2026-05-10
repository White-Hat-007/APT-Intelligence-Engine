# Advanced Persistent Threat (APT) Intelligence Engine

<div align="center">
  <h3>A Real-Time, Multi-Modal Telemetry Ingestion and Behavioral Analysis Framework</h3>
  <i>Engineering threat intelligence through deterministic clustering and adversarial fingerprinting.</i>
</div>

---

## 🛑 EXECUTIVE OVERVIEW

The **Advanced Persistent Threat (APT) Intelligence Engine** is a high-performance, modular framework designed for the real-time ingestion, normalization, and behavioral analysis of multi-modal security telemetry. Moving beyond static Indicators of Compromise (IoCs), this engine leverages adversarial behavioral fingerprinting, MITRE ATT&CK mapping, and unsupervised machine learning (K-Means clustering) to identify, track, and correlate complex intrusion campaigns across disparate data sources.

Developed with a security-first, extensible architecture, the engine seamlessly integrates with enterprise SOC infrastructure (Splunk, ELK, Kafka) to provide immediate tactical insights and strategic intelligence reporting.

## 🧬 CORE ARCHITECTURE & COMPONENTS

The engine operates on a pipeline architecture consisting of four primary stages: Ingestion, Mapping, Analytics, and Reporting.

### 1. Telemetry Ingestion Subsystem (`ingestion/`)
A thread-safe, scalable streaming engine capable of processing high-velocity event streams via sliding windows or batch configurations.

*   **Real-Time Ingestor (`realtime_ingestor.py`):** The core ingestion loop utilizing concurrent worker threads and deque-based buffers for non-blocking event processing. Supports dynamic batch sizing and sliding time windows.
*   **Enterprise Connectors (`connectors.py`):** Pluggable generator functions supporting native integration with Kafka, Elasticsearch, Splunk, REST APIs, WebSockets, Syslog, and Windows Event Logs.

**Example: Kafka Connector Integration**
```python
def kafka_event_stream(
    topic: str,
    bootstrap_servers: List[str],
    group_id: str = "threat-intelligence-engine",
) -> Generator[Dict[str, Any], None, None]:
    # ... connection logic ...
    for message in consumer:
        raw_event = message.value
        # Normalize to standard schema
        yield {
            "campaign_id": raw_event.get("campaign_id", "KAFKA-STREAM"),
            "event_id": raw_event.get("event_id", str(uuid.uuid4())),
            "timestamp": raw_event.get("timestamp", str(datetime.now(timezone.utc))),
            "host": raw_event.get("host", "UNKNOWN"),
            "technique_id": raw_event.get("technique_id", None),
            "source": "kafka",
            "_raw": raw_event,
        }
```

*   **Sysmon Parser (`sysmon_parser.py`):** Deterministic parser for inferring adversarial techniques from raw Sysmon logs.

**Example: Deterministic Technique Inference**
```python
def infer_technique(event):
    event_id = event.get("EventID")
    command = str(event.get("CommandLine", "")).lower()

    # Process Creation (Event ID 1)
    if event_id == 1:
        # Encoded PowerShell -> Execution (T1059)
        if "powershell" in image and "-enc" in command:
            return "T1059"
        # Mimikatz execution -> Credential Dumping (T1003)
        if "mimikatz" in command:
            return "T1003"
    
    # Network Connection (Event ID 3) -> Exfiltration (T1041)
    if event_id == 3:
        return "T1041"
    
    return None
```

### 2. Adversarial Mapping Layer (`mapping/`)
*   **MITRE ATT&CK Mapper (`mitre_mapper.py`):** Normalizes disparate event streams by translating raw telemetry and inferred techniques into standardized MITRE ATT&CK tactics (e.g., Execution, Persistence, Credential Access).

### 3. Analytics & Fingerprinting Engine (`analytics/`)
The computational core responsible for translating discrete events into actionable intelligence.

*   **Fingerprint Engine (`fingerprint_engine.py`):** Generates fixed-length behavioral vectors representing adversary behavior. Computes technique frequency, tactic sequences, host spread, and a proprietary **Campaign Complexity Score**.

**Example: Behavioral Vectorization**
```python
# Fixed-length vectorization mapping
ALL_TECHNIQUES = ["T1059", "T1547", "T1003", "T1021", "T1041"]

def generate_fingerprint(mapped_logs):
    techniques = [e["technique_id"] for e in mapped_logs]
    hosts = set(e["host"] for e in mapped_logs)
    technique_freq = Counter(techniques)

    # TRUE BEHAVIORAL VECTOR (Technique-based)
    # Each dimension represents frequency of a specific technique
    vector = np.array([
        technique_freq.get(t, 0) for t in ALL_TECHNIQUES
    ])
    
    # Behavioral complexity metric
    complexity_score = len(set(techniques)) * len(hosts)
    
    # ... returns comprehensive fingerprint dict ...
```

*   **Clustering Engine (`clustering_engine.py`):** Utilizes `scikit-learn` K-Means clustering on behavioral vectors to group structurally similar campaigns and identify threat actor overlap.

**Example: K-Means Clustering on Behavioral Vectors**
```python
from sklearn.cluster import KMeans
import numpy as np

def cluster_campaigns(fingerprints, n_clusters=2):
    # Extract behavioral vectors
    vectors = np.array([fp["vector"] for fp in fingerprints])

    # Dynamic cluster adjustment based on distinct vectors
    if len(set(map(tuple, vectors))) < n_clusters:
        n_clusters = len(set(map(tuple, vectors)))

    # Execute K-Means clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    return labels
```

*   **Similarity Engine (`similarity_engine.py`):** Calculates cosine similarity between campaign vectors to quantify operational divergence.

**Example: Quantifying Campaign Divergence**
```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def compute_similarity(fp1, fp2):
    # Reshape behavioral vectors for scikit-learn
    v1 = np.array(fp1["vector"]).reshape(1, -1)
    v2 = np.array(fp2["vector"]).reshape(1, -1)

    # Compute cosine similarity score (1.0 = identical, 0.0 = completely divergent)
    score = cosine_similarity(v1, v2)[0][0]
    return score
```

*   **Graph Builder (`graph_builder.py`):** Constructs directed graphs using `networkx` to visualize the chronological progression and relationship of attack techniques within a campaign.

**Example: Building Attack Progression Graphs**
```python
import networkx as nx

def build_attack_graph(mapped_logs):
    G = nx.DiGraph()

    # Map sequential technique transitions as directed edges
    for i in range(len(mapped_logs)-1):
        src = mapped_logs[i]["technique_id"]
        dst = mapped_logs[i+1]["technique_id"]
        G.add_edge(src, dst)

    return G
```

### 4. Intelligence Reporting (`reporting/`)
*   **Report Generator (`intelligence_report.py`):** Synthesizes analytical outputs into strategic threat intelligence reports, detailing risk levels, cluster classifications, and behavioral assessments.

---

## ⚙️ OPERATIONAL MODES

The engine supports multiple operational paradigms, configurable via the `MODE` directive in `main.py`:

```python
# ==========================================
# CONFIGURATION (main.py)
# ==========================================
# "simulate"  → synthetic campaigns (batch mode)
# "sysmon"    → real Sysmon ingestion (batch mode)
# "realtime"  → real-time streaming ingestion (simulated)
# "kafka"     → Kafka streaming
# "splunk"    → Splunk integration
MODE = "realtime"
```

## 🛠️ DEPLOYMENT & CONFIGURATION

### Prerequisites
Install the required dependencies based on your desired operational mode:

```bash
# Core Dependencies
pip install pandas scikit-learn networkx numpy jinja2

# Connector Dependencies (Install as needed)
pip install kafka-python elasticsearch splunk-sdk requests websocket-client
```

### Enterprise Configurations
Modify `CONNECTOR_CONFIG` in `main.py` with your enterprise credentials. Refer to `ENDPOINT_CONFIGURATIONS.py` for comprehensive examples.

**Example: Hybrid Cloud/On-Prem Setup**
```python
CONNECTOR_CONFIG = {
    "splunk": {
        "host": "splunk.internal.local:8089",
        "username": "threat_intel",
        "password": "SecurePassword123", # Use env vars in prod
        "search_query": "sourcetype=sysmon index=main earliest=-30m latest=now"
    },
    "kafka": {
        "bootstrap_servers": ["kafka1.cloud.local:9092", "kafka2.cloud.local:9092"],
        "topic": "security.alerts",
        "group_id": "apt_threat_intelligence"
    }
}
```

### Executing the Engine

**1. Interactive Demo (`connector_demo.py`)**
For a quick overview of all supported enterprise integrations and configurations, run the interactive demo:
```bash
python connector_demo.py
```
This utility provides a terminal UI comparing connector speed, scale, and specific deployment commands.

**2. Main Pipeline Execution (`main.py`)**
To run the engine in your configured mode (batch, simulated, or live connector):
```bash
python main.py
```

### Testing Infrastructure
The project includes a suite of mock servers to validate the ingestion pipeline without requiring access to production systems:
```bash
# Start all mock servers (REST, WebSocket, Splunk)
python setup_infrastructure.py

# Send simulated Syslog events to test ingestion
python send_syslog.py localhost 514 10
```

---

## 🔬 ANALYTICAL METHODOLOGY: BEHAVIORAL VECTORIZATION

The engine departs from traditional signature matching by employing **Behavioral Vectorization**.

1.  **Extraction:** Telemetry is parsed to identify execution artifacts, network connections, and registry modifications.
2.  **Inference:** Artifacts are mapped to specific MITRE ATT&CK techniques (e.g., PowerShell execution with obfuscation -> T1059).
3.  **Vectorization:** Techniques are compiled into a frequency distribution vector across a predefined technique universe.
4.  **Clustering:** Vectors are mapped into n-dimensional space. K-Means clustering identifies centroids representing distinct operational playbooks, enabling the correlation of seemingly disparate campaigns attributed to the same threat actor.

## ⚠️ SECURITY CONSIDERATIONS
*   **Credential Management:** Never hardcode credentials in `CONNECTOR_CONFIG` or `ENDPOINT_CONFIGURATIONS.py`. Utilize environment variables or secure vault integrations for production deployments.
*   **Data Privacy:** Ensure appropriate anonymization or masking is applied to telemetry streams if processing PII or sensitive hostnames.

---
*Developed for advanced threat hunting and proactive adversary characterization.*
