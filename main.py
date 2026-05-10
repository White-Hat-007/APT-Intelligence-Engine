import json
import os
import time
import sys
from typing import Optional

from ingestion.simulator import simulate_campaign
from ingestion.sysmon_parser import parse_sysmon_log
from ingestion.realtime_ingestor import RealTimeIngestor, create_simulated_event_stream
from ingestion.connectors import (
    kafka_event_stream,
    websocket_event_stream,
    rest_poll_event_stream,
    splunk_event_stream,
    elastic_event_stream,
    syslog_event_stream,
    windows_eventlog_stream,
    get_connector,
)
from mapping.mitre_mapper import map_to_tactics
from analytics.fingerprint_engine import generate_fingerprint
from analytics.clustering_engine import cluster_campaigns
from analytics.similarity_engine import compute_similarity
from reporting.intelligence_report import generate_report


# ==========================================
# CONFIGURATION
# ==========================================

DATA_DIR = "data"
LOGS_DIR = "logs"

NUM_CAMPAIGNS = 3

# "simulate"  → synthetic campaigns (batch mode)
# "sysmon"    → real Sysmon ingestion (batch mode)
# "realtime"  → real-time streaming ingestion (simulated)
# "kafka"     → Kafka streaming (requires kafka-python)
# "websocket" → WebSocket streaming (requires websocket-client)
# "rest"      → REST API polling (requires requests)
# "splunk"    → Splunk integration (requires splunk-sdk)
# "elastic"   → Elasticsearch streaming (requires elasticsearch)
# "syslog"    → Syslog listening (standard library)
# "windows_eventlog" → Windows Event Log (requires pywin32, Windows only)
MODE = "realtime"

SYSMON_FILE = os.path.join(LOGS_DIR, "sample_sysmon.json")

# Real-time ingestion config
REALTIME_BATCH_SIZE = 10  # Process every N events
REALTIME_TIME_WINDOW = 3.0  # Or every N seconds
REALTIME_DURATION = 30  # Run realtime pipeline for N seconds

# Real-world connector configurations
CONNECTOR_CONFIG = {
    # Kafka
    "kafka": {
        "topic": "security_events",
        "bootstrap_servers": ["kafka:9092"],
        "group_id": "threat-intelligence-engine",
    },
    # WebSocket
    "websocket": {
        "url": "wss://siem.local:8080/events",
        "max_retries": 3,
        "reconnect_delay": 2.0,
    },
    # REST API
    "rest": {
        "api_url": "https://api.siem.local/api/events",
        "poll_interval": 10.0,
        "auth_token": "your_bearer_token",
    },
    # Splunk
    "splunk": {
        "host": "splunk.local:8089",
        "username": "admin",
        "password": "password",
        "search_query": "sourcetype=sysmon EventCode=1 | fields host, process",
    },
    # Elasticsearch
    "elastic": {
        "hosts": ["localhost:9200"],
        "index_pattern": "logs-sysmon-*",
        "query": {"query": {"match_all": {}}},
    },
    # Syslog
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp",
    },
    # Windows Event Log
    "windows_eventlog": {
        "log_name": "Security",
    },
}


# ==========================================
# UTILITIES
# ==========================================

def ensure_directories():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)


def run_single_campaign(index):
    """
    Execute one campaign either via:
    - Simulation
    - Real Sysmon ingestion
    """

    if MODE == "simulate":
        logs = simulate_campaign(index)

        output_file = os.path.join(DATA_DIR, f"campaign_{index}.json")

        with open(output_file, "w") as f:
            json.dump(logs, f, indent=4)

        mapped_logs = map_to_tactics(logs)

    elif MODE == "sysmon":
        if not os.path.exists(SYSMON_FILE):
            raise FileNotFoundError(
                f"Sysmon file not found at: {SYSMON_FILE}"
            )

        logs = parse_sysmon_log(SYSMON_FILE)
        mapped_logs = map_to_tactics(logs)

    else:
        raise ValueError("Invalid MODE. Use 'simulate' or 'sysmon'.")

    fingerprint = generate_fingerprint(mapped_logs)
    return fingerprint


def print_similarity_matrix(fingerprints):
    print("\n=== CAMPAIGN SIMILARITY MATRIX (Cosine Similarity) ===\n")

    size = len(fingerprints)
    column_width = 10
    row_label_width = 8

    # Header
    header = " " * row_label_width
    for j in range(size):
        header += f"{('C' + str(j+1)):>{column_width}}"
    print(header)

    # Divider
    print(" " * row_label_width + "-" * (column_width * size))

    # Rows
    for i in range(size):
        row = f"{('C' + str(i+1)):<{row_label_width}}"
        for j in range(size):
            score = compute_similarity(fingerprints[i], fingerprints[j])
            row += f"{score:>{column_width}.2f}"
        print(row)


# ==========================================
# REAL-TIME INGESTION FUNCTIONS
# ==========================================

class RealtimeAnalyticsContext:
    """Context for real-time analytics to maintain state across batches."""
    
    def __init__(self):
        self.all_events = []
        self.batch_fingerprints = []
        self.batch_count = 0
    
    def on_batch_ready(self, batch_events):
        """Callback when a batch of events is ready for processing."""
        self.batch_count += 1
        
        # Store all events
        self.all_events.extend(batch_events)
        
        # Map to tactics
        mapped_events = map_to_tactics(batch_events)
        
        # Generate fingerprint for this batch
        fingerprint = generate_fingerprint(mapped_events)
        self.batch_fingerprints.append(fingerprint)
        
        print(f"\n[REALTIME] Batch #{self.batch_count} processed ({len(batch_events)} events)")
        print(f"  Techniques: {fingerprint['unique_techniques']}")
        print(f"  Hosts: {fingerprint['affected_hosts']}")
        print(f"  Complexity: {fingerprint['campaign_complexity_score']}")
    
    def get_summary(self):
        """Get analysis summary from realtime processing."""
        if not self.batch_fingerprints:
            return {}
        
        # Aggregate fingerprints across batches
        aggregated = self.batch_fingerprints[0] if len(self.batch_fingerprints) == 1 else aggregate_fingerprints(
            self.batch_fingerprints
        )
        
        return {
            "total_events": len(self.all_events),
            "total_batches": self.batch_count,
            "aggregated_fingerprint": aggregated,
        }


def aggregate_fingerprints(fingerprints):
    """
    Aggregate multiple fingerprints into a single consolidated fingerprint.
    Useful for real-time batch processing.
    """
    import numpy as np
    from collections import Counter
    
    all_techniques = []
    all_tactics = []
    all_hosts = set()
    
    for fp in fingerprints:
        all_techniques.extend(fp["unique_techniques"])
        all_tactics.extend(fp["tactic_frequency"].keys())
        all_hosts.update(fp["affected_hosts"])
    
    technique_freq = Counter(all_techniques)
    tactic_freq = Counter(all_tactics)
    
    # Re-vectorize aggregated data
    from analytics.fingerprint_engine import ALL_TECHNIQUES
    vector = np.array([
        technique_freq.get(t, 0) for t in ALL_TECHNIQUES
    ])
    
    complexity_score = len(set(all_techniques)) * len(all_hosts)
    
    return {
        "unique_techniques": list(set(all_techniques)),
        "technique_frequency": dict(technique_freq),
        "tactic_frequency": dict(tactic_freq),
        "affected_hosts": list(all_hosts),
        "campaign_complexity_score": complexity_score,
        "vector": vector
    }


def run_realtime_pipeline(
    campaign_id="RT-CAMPAIGN-1",
    batch_size=REALTIME_BATCH_SIZE,
    time_window=REALTIME_TIME_WINDOW,
    duration=REALTIME_DURATION
):
    """
    Execute real-time streaming ingestion pipeline.
    
    Args:
        campaign_id: Campaign identifier
        batch_size: Events per batch
        time_window: Time window for sliding window (seconds)
        duration: Total runtime (seconds)
    """
    print(f"\n========== REALTIME INGESTION PIPELINE ==========")
    print(f"Campaign: {campaign_id}")
    print(f"Batch Size: {batch_size} events")
    print(f"Time Window: {time_window}s")
    print(f"Duration: {duration}s\n")
    
    # Create analytics context
    ctx = RealtimeAnalyticsContext()
    
    # Create ingestor with config
    ingestor = RealTimeIngestor(
        batch_size=batch_size,
        time_window_seconds=time_window,
        max_queue_size=500
    )
    
    # Register batch processing callback
    ingestor.register_batch_callback(ctx.on_batch_ready)
    
    # Create simulated event stream (pluggable source)
    num_events = int((duration / time_window) * batch_size * 1.5)  # Estimate
    event_source = create_simulated_event_stream(
        campaign_id=campaign_id,
        num_events=num_events,
        delay_seconds=0.05
    )
    
    ingestor.set_event_source(event_source)
    
    # Start processing
    ingestor.start()
    
    # Run for specified duration
    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            time.sleep(1)
            stats = ingestor.get_stats()
            print(f"[STATS] Events: {stats['total_events_ingested']}, "
                  f"Batches: {stats['total_batches_processed']}, "
                  f"Queue: {stats['queue_size']}")
    except KeyboardInterrupt:
        print("\n[REALTIME] Interrupted by user")
    finally:
        ingestor.stop()
    
    # Get summary and report
    summary = ctx.get_summary()
    
    if summary:
        fp = summary["aggregated_fingerprint"]
        print(f"\n========== REALTIME ANALYSIS SUMMARY ==========")
        print(f"Total Events Processed: {summary['total_events']}")
        print(f"Total Batches: {summary['total_batches']}")
        print(f"\n========== INTELLIGENCE REPORT ==========")
        report = generate_report(fp, cluster_label=0)
        print(report)
    
    return ctx


def run_connector_pipeline(
    connector_type: str,
    batch_size: int = REALTIME_BATCH_SIZE,
    time_window: float = REALTIME_TIME_WINDOW,
    duration: float = REALTIME_DURATION,
    config: Optional[dict] = None,
):
    """
    Execute real-time streaming from real-world connector.
    
    Args:
        connector_type: 'kafka', 'websocket', 'rest', 'splunk', 'elastic', 'syslog', 'windows_eventlog'
        batch_size: Events per batch
        time_window: Time window for sliding window (seconds)
        duration: Total runtime (seconds), 0 for infinite
        config: Connector-specific configuration
    """
    if config is None:
        config = CONNECTOR_CONFIG.get(connector_type, {})
    
    print(f"\n========== {connector_type.upper()} INGESTION PIPELINE ==========")
    print(f"Connector: {connector_type}")
    print(f"Batch Size: {batch_size} events")
    print(f"Time Window: {time_window}s")
    if duration > 0:
        print(f"Duration: {duration}s")
    else:
        print(f"Duration: INFINITE (Ctrl+C to stop)")
    print(f"Configuration: {config}\n")
    
    # Validate connector type
    valid_connectors = [
        'kafka', 'websocket', 'rest', 'splunk', 'elastic', 'syslog', 'windows_eventlog'
    ]
    if connector_type not in valid_connectors:
        raise ValueError(
            f"Invalid connector: {connector_type}. "
            f"Valid options: {', '.join(valid_connectors)}"
        )
    
    # Create analytics context
    ctx = RealtimeAnalyticsContext()
    
    # Create ingestor
    ingestor = RealTimeIngestor(
        batch_size=batch_size,
        time_window_seconds=time_window,
        max_queue_size=500
    )
    
    # Register batch processing callback
    ingestor.register_batch_callback(ctx.on_batch_ready)
    
    # Create event source from connector
    try:
        print(f"[CONNECTOR] Initializing {connector_type}...")
        event_source = get_connector(connector_type, **config)
        ingestor.set_event_source(event_source)
    except Exception as e:
        print(f"[ERROR] Failed to initialize {connector_type}: {e}")
        print(f"[ERROR] Check that required dependencies are installed")
        print(f"[ERROR] Verify configuration in CONNECTOR_CONFIG")
        raise
    
    # Start processing
    ingestor.start()
    
    # Run for specified duration
    start_time = time.time()
    try:
        while True:
            if duration > 0 and time.time() - start_time > duration:
                break
            
            time.sleep(1)
            stats = ingestor.get_stats()
            print(f"[STATS] Events: {stats['total_events_ingested']}, "
                  f"Batches: {stats['total_batches_processed']}, "
                  f"Buffer: {stats['current_buffer_size']}, "
                  f"Queue: {stats['queue_size']}")
    except KeyboardInterrupt:
        print(f"\n[{connector_type.upper()}] Interrupted by user")
    finally:
        ingestor.stop()
    
    # Get summary and report
    summary = ctx.get_summary()
    
    if summary:
        fp = summary["aggregated_fingerprint"]
        print(f"\n========== ANALYSIS SUMMARY ({connector_type.upper()}) ==========")
        print(f"Total Events Processed: {summary['total_events']}")
        print(f"Total Batches: {summary['total_batches']}")
        print(f"\n========== INTELLIGENCE REPORT ==========")
        report = generate_report(fp, cluster_label=0)
        print(report)
    
    return ctx


# ==========================================
# MAIN PIPELINE
# ==========================================

def main():
    print("\n========== APT Threat Intelligence Engine ==========\n")
    print(f"Operating Mode: {MODE.upper()}\n")

    ensure_directories()

    if MODE == "simulate":
        print("[BATCH MODE] Running synthetic campaign simulations...\n")
        
        fingerprints = []
        for i in range(NUM_CAMPAIGNS):
            print(f"Running Simulation {i + 1}...")
            fp = run_single_campaign(i)
            fingerprints.append(fp)

        # Clustering (only if multiple campaigns)
        if len(fingerprints) > 1:
            labels = cluster_campaigns(fingerprints, n_clusters=2)
        else:
            labels = [0]

        # Reporting
        for idx, fp in enumerate(fingerprints):
            print(f"\n========== INTELLIGENCE REPORT - Campaign {idx + 1} ==========")
            print(f"Cluster Group: {labels[idx]}")
            report = generate_report(fp, labels[idx])
            print(report)

        # Similarity matrix
        if len(fingerprints) > 1:
            print_similarity_matrix(fingerprints)

    elif MODE == "sysmon":
        print("[BATCH MODE] Ingesting Sysmon logs...\n")
        
        fingerprints = []
        print("Ingesting Sysmon Log...")
        fp = run_single_campaign(0)
        fingerprints.append(fp)

        # Clustering
        labels = [0]

        # Reporting
        for idx, fp in enumerate(fingerprints):
            print(f"\n========== INTELLIGENCE REPORT - Sysmon Analysis ==========")
            print(f"Cluster Group: {labels[idx]}")
            report = generate_report(fp, labels[idx])
            print(report)

    elif MODE == "realtime":
        print("[STREAMING MODE] Starting real-time ingestion pipeline...\n")
        
        ctx = run_realtime_pipeline(
            campaign_id="REALTIME-CAMPAIGN-001",
            batch_size=REALTIME_BATCH_SIZE,
            time_window=REALTIME_TIME_WINDOW,
            duration=REALTIME_DURATION
        )
        
        # Optional: cluster results from realtime session
        if len(ctx.batch_fingerprints) > 1:
            print("\n========== REALTIME CLUSTERING ANALYSIS ==========")
            labels = cluster_campaigns(ctx.batch_fingerprints, n_clusters=min(2, len(ctx.batch_fingerprints)))
            for idx, fp in enumerate(ctx.batch_fingerprints):
                print(f"Batch #{idx + 1} → Cluster {labels[idx]}")

    elif MODE in ["kafka", "websocket", "rest", "splunk", "elastic", "syslog", "windows_eventlog"]:
        print(f"[CONNECTOR MODE] Starting {MODE.upper()} ingestion pipeline...\n")
        
        # Update default duration for connectors (use 0 for infinite)
        connector_duration = 0  # Run indefinitely until Ctrl+C
        
        ctx = run_connector_pipeline(
            connector_type=MODE,
            batch_size=REALTIME_BATCH_SIZE,
            time_window=REALTIME_TIME_WINDOW,
            duration=connector_duration,
            config=CONNECTOR_CONFIG.get(MODE)
        )
        
        # Optional: cluster results
        if len(ctx.batch_fingerprints) > 1:
            print(f"\n========== {MODE.upper()} CLUSTERING ANALYSIS ==========")
            labels = cluster_campaigns(ctx.batch_fingerprints, n_clusters=min(2, len(ctx.batch_fingerprints)))
            for idx, fp in enumerate(ctx.batch_fingerprints):
                print(f"Batch #{idx + 1} → Cluster {labels[idx]}")

    else:
        raise ValueError(
            f"Invalid MODE: {MODE}\n"
            f"Valid options:\n"
            f"  - simulate (synthetic campaigns)\n"
            f"  - sysmon (static Sysmon logs)\n"
            f"  - realtime (simulated streaming)\n"
            f"  - kafka (Apache Kafka)\n"
            f"  - websocket (WebSocket endpoints)\n"
            f"  - rest (REST API polling)\n"
            f"  - splunk (Splunk integration)\n"
            f"  - elastic (Elasticsearch)\n"
            f"  - syslog (Syslog listener)\n"
            f"  - windows_eventlog (Windows Event Log)"
        )

    print("\n========== Analysis Complete ==========\n")


if __name__ == "__main__":
    main()