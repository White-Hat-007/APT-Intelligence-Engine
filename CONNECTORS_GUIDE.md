# Real-World Data Connectors Guide

## Overview

The APT Threat Intelligence Engine now supports **7 real-world data connectors** enabling integration with enterprise security infrastructure:

| Connector | Type | Status | Use Case |
|-----------|------|--------|----------|
| **Kafka** | Message Queue | ✅ Ready | High-volume event streaming |
| **WebSocket** | Real-Time | ✅ Ready | Live event feeds from APIs |
| **REST API** | HTTP Polling | ✅ Ready | Cloud SIEMs, REST endpoints |
| **Splunk** | SIEM | ✅ Ready | Splunk Enterprise instances |
| **Elasticsearch** | Search Engine | ✅ Ready | ELK Stack, Elastic Cloud |
| **Syslog** | Protocol | ✅ Ready | Traditional syslog servers, network devices |
| **Windows Event Log** | Local | ✅ Ready | Windows systems (Windows only) |

---

## Quick Start

### 1. Kafka Integration

**Installation**:
```bash
pip install kafka-python
```

**Configuration** (in `main.py`):
```python
MODE = "kafka"

CONNECTOR_CONFIG["kafka"] = {
    "topic": "security_events",
    "bootstrap_servers": ["kafka1:9092", "kafka2:9092"],
    "group_id": "threat-intelligence-engine",
}
```

**Run**:
```bash
python main.py
```

**Event Format Expected**:
```json
{
    "campaign_id": "CAMPAIGN-001",
    "event_id": "uuid",
    "timestamp": "2026-02-27T12:00:00Z",
    "host": "SERVER-01",
    "technique_id": "T1059"
}
```

---

### 2. WebSocket Integration

**Installation**:
```bash
pip install websocket-client
```

**Configuration**:
```python
MODE = "websocket"

CONNECTOR_CONFIG["websocket"] = {
    "url": "wss://siem.company.local:8080/events",
    "max_retries": 3,
    "reconnect_delay": 2.0,
}
```

**Run**:
```bash
python main.py
```

**Server-Side Example** (Flask):
```python
from flask import Flask
from flask_sockets import Sockets
import json

app = Flask(__name__)
sockets = Sockets(app)

@sockets.route('/echo')
def echo_socket(ws):
    while not ws.closed:
        message = ws.receive()
        if message:
            event = json.loads(message)
            ws.send(json.dumps(event))
```

---

### 3. REST API Polling

**Installation**:
```bash
pip install requests
```

**Configuration**:
```python
MODE = "rest"

CONNECTOR_CONFIG["rest"] = {
    "api_url": "https://api.siem.company.local/api/events",
    "poll_interval": 10.0,  # Seconds between polls
    "auth_token": "your_bearer_token_here",
}
```

**Run**:
```bash
python main.py
```

**API Endpoint Expected**:
```
GET /api/events
Authorization: Bearer your_token

Response:
[
    {
        "event_id": "uuid",
        "campaign_id": "CAMPAIGN-001",
        "timestamp": "2026-02-27T12:00:00Z",
        "host": "SERVER-01",
        "technique_id": "T1059"
    },
    ...
]
```

---

### 4. Splunk Integration

**Installation**:
```bash
pip install splunk-sdk
```

**Configuration**:
```python
MODE = "splunk"

CONNECTOR_CONFIG["splunk"] = {
    "host": "splunk.company.local:8089",
    "username": "admin",
    "password": "splunk_password",
    "search_query": "sourcetype=sysmon EventCode=1 | fields host, process_name",
}
```

**Run**:
```bash
python main.py
```

**Splunk Search Query Examples**:
```spl
# Process creation events
sourcetype=sysmon EventCode=1 | fields host, process_name, parent_process

# Lateral movement indicators
(EventCode=3 OR EventCode=22) host::* | fields host, destination_ip, port

# Credential access events
EventCode=10 OR EventCode=11 | fields host, target_process

# Custom fields mapping
sourcetype=sysmon | eval technique_id=case(EventCode=1, "T1059", EventCode=3, "T1021") | fields host, technique_id
```

---

### 5. Elasticsearch Integration

**Installation**:
```bash
pip install elasticsearch
```

**Configuration**:
```python
MODE = "elastic"

CONNECTOR_CONFIG["elastic"] = {
    "hosts": ["elasticsearch.company.local:9200"],
    "index_pattern": "logs-sysmon-*",
    "query": {
        "query": {
            "bool": {
                "must": [
                    {"term": {"event.category": "process"}},
                    {"range": {"@timestamp": {"gte": "now-1h"}}}
                ]
            }
        }
    },
    "username": "elastic_user",
    "password": "elastic_password",
}
```

**Run**:
```bash
python main.py
```

**Index Mapping Example**:
```json
{
    "mappings": {
        "properties": {
            "event_id": {"type": "keyword"},
            "campaign_id": {"type": "keyword"},
            "host": {"type": "keyword"},
            "technique_id": {"type": "keyword"},
            "@timestamp": {"type": "date"},
            "process_name": {"type": "text"}
        }
    }
}
```

---

### 6. Syslog Listener

**Installation**:
```bash
# No external dependencies required (uses standard library)
```

**Configuration**:
```python
MODE = "syslog"

CONNECTOR_CONFIG["syslog"] = {
    "host": "0.0.0.0",  # Listen on all interfaces
    "port": 514,
    "protocol": "udp",  # or "tcp"
}
```

**Run**:
```bash
python main.py
```

**Send Test Messages**:
```bash
# UDP
echo "<134>test message" | nc -u localhost 514

# TCP
echo "<134>test message" | nc localhost 514

# Using logger utility
logger -h localhost -P 514 "test event"
```

**Syslog Message Format**:
```
<PRI>TIMESTAMP HOSTNAME TAG[PID]: MESSAGE
<134>Feb 27 12:00:00 server01 sysmon: Process created
```

---

### 7. Windows Event Log

**Installation** (Windows only):
```bash
pip install pywin32
```

**Configuration**:
```python
MODE = "windows_eventlog"

CONNECTOR_CONFIG["windows_eventlog"] = {
    "log_name": "Security",  # or "System", "Application"
}
```

**Run** (Administrator required):
```bash
python main.py
```

**Monitored Event Logs**:
- `Security`: Authentication, privilege use, object access
- `System`: System events, driver loading, service start/stop
- `Application`: Application errors, custom events
- `Microsoft-Windows-Sysmon/Operational`: Process creation, network connections

---

## Configuration Details

### Standard Event Schema

All connectors normalize events to this schema:

```python
{
    "campaign_id": str,          # Mission/campaign identifier
    "event_id": str,             # Unique event identifier (UUID)
    "timestamp": str,            # ISO 8601 timestamp
    "host": str,                 # Source host/system
    "technique_id": str,         # MITRE ATT&CK ID (e.g., T1059)
    "source": str,               # Connector type (kafka, splunk, etc)
    "_raw": dict                 # Original event for debugging
}
```

### Batch Processing

All connectors integrate with real-time batching:

```python
REALTIME_BATCH_SIZE = 10        # Process every 10 events
REALTIME_TIME_WINDOW = 3.0      # OR every 3 seconds
REALTIME_DURATION = 0           # 0 = run indefinitely
```

### Error Handling

- **Kafka**: Exponential backoff on connection failures
- **WebSocket**: Automatic reconnection with configurable delay
- **REST**: Retry logic with exponential backoff
- **Splunk**: Job monitoring and timeout handling
- **Elasticsearch**: Scroll API for large result sets
- **Syslog**: Graceful message parsing with skip-on-error
- **Windows EventLog**: Continuous polling with error recovery

---

## Advanced Usage

### Custom Event Mapping

Create a mapping function for your data source:

```python
def splunk_to_standard_event(splunk_result):
    """Map Splunk fields to standard schema."""
    return {
        "campaign_id": "SPLUNK-FEED",
        "event_id": splunk_result.get("_raw"),
        "timestamp": splunk_result.get("_time"),
        "host": splunk_result.get("host"),
        "technique_id": splunk_result.get("mitre_technique"),
        "source": "splunk",
        "_raw": splunk_result,
    }
```

### Multi-Source Streaming

Create a combined generator:

```python
def multi_source_stream():
    """Stream from both Kafka and REST API."""
    kafka_source = kafka_event_stream(**CONNECTOR_CONFIG["kafka"])
    rest_source = rest_poll_event_stream(**CONNECTOR_CONFIG["rest"])
    
    for event in kafka_source:
        yield event
    
    for event in rest_source:
        yield event
```

### Filtering and Preprocessing

```python
def filtered_event_stream(connector_type, **config):
    """Stream with filtering applied."""
    source = get_connector(connector_type, **config)
    
    for event in source:
        # Skip events without technique mapping
        if event.get("technique_id") is None:
            continue
        
        # Skip noise
        if "test" in event.get("host", "").lower():
            continue
        
        yield event
```

---

## Monitoring & Troubleshooting

### Check Event Flow

```python
# In REPL
from ingestion.realtime_ingestor import RealTimeIngestor
from ingestion.connectors import get_connector

# Create test stream
source = get_connector('rest', api_url='http://localhost:8000/events')

# Verify first events
for i, event in enumerate(source):
    print(event)
    if i >= 5:
        break
```

### Monitor Batch Processing

```python
# Watch stats in real-time
ingestor = RealTimeIngestor(batch_size=10)

while True:
    stats = ingestor.get_stats()
    print(f"Events: {stats['total_events_ingested']}, "
          f"Batches: {stats['total_batches_processed']}")
    time.sleep(1)
```

### Debug Missing Technique Mapping

```python
# Find unmapped events
def custom_callback(batch_events):
    unmapped = [e for e in batch_events if e.get("technique_id") is None]
    if unmapped:
        print(f"⚠️ {len(unmapped)} unmapped events:")
        for e in unmapped:
            print(f"  - {e.get('_raw')}")
```

---

## Performance Characteristics

| Connector | Throughput | Latency | Memory | Reliability |
|-----------|-----------|---------|--------|-------------|
| **Kafka** | 10k-100k events/s | <100ms | Low | Very High |
| **WebSocket** | 1k-10k events/s | <50ms | Low | High |
| **REST** | 100-1k events/s | 1-10s | Low | Medium |
| **Splunk** | 100-1k events/s | 1-5s | Medium | High |
| **Elasticsearch** | 1k-10k events/s | 100-500ms | Medium | High |
| **Syslog** | 1k-10k events/s | <10ms | Low | High |
| **Windows EventLog** | 100-1k events/s | 100-500ms | Low | Medium |

---

## Dependencies Summary

| Connector | Package | Command |
|-----------|---------|---------|
| Kafka | kafka-python | `pip install kafka-python` |
| WebSocket | websocket-client | `pip install websocket-client` |
| REST | requests | `pip install requests` |
| Splunk | splunk-sdk | `pip install splunk-sdk` |
| Elasticsearch | elasticsearch | `pip install elasticsearch` |
| Syslog | *stdlib* | (No install needed) |
| Windows EventLog | pywin32 | `pip install pywin32` |

---

## Security Best Practices

1. **Never hardcode credentials**:
   ```python
   # ❌ BAD
   CONNECTOR_CONFIG["splunk"]["password"] = "admin123"
   
   # ✅ GOOD
   import os
   CONNECTOR_CONFIG["splunk"]["password"] = os.getenv("SPLUNK_PASSWORD")
   ```

2. **Use HTTPS for REST APIs**:
   ```python
   CONNECTOR_CONFIG["rest"]["api_url"] = "https://api.siem.local/events"
   ```

3. **Enable authentication**:
   ```python
   CONNECTOR_CONFIG["elastic"] = {
       "hosts": ["elasticsearch:9200"],
       "username": "elastic_user",
       "password": os.getenv("ES_PASSWORD"),
   }
   ```

4. **Validate certificates**:
   ```python
   # Verify SSL certificates (default: True)
   # Set to False only for testing with self-signed certs
   ```

5. **Rotate access tokens regularly**:
   ```python
   CONNECTOR_CONFIG["rest"]["auth_token"] = os.getenv("API_TOKEN")
   # Rotate token periodically
   ```

---

## Factory Function

Use the `get_connector()` factory for dynamic connector selection:

```python
from ingestion.connectors import get_connector

# Dynamic selection
connector_type = input("Enter connector (kafka/websocket/rest/splunk/elastic/syslog/windows_eventlog): ")
source = get_connector(connector_type, **CONNECTOR_CONFIG[connector_type])

for event in source:
    print(event)
```

---

## Compatibility Matrix

| Connector | Python 3.8+ | Windows | Linux | macOS | Docker |
|-----------|------------|---------|-------|-------|--------|
| Kafka | ✅ | ✅ | ✅ | ✅ | ✅ |
| WebSocket | ✅ | ✅ | ✅ | ✅ | ✅ |
| REST | ✅ | ✅ | ✅ | ✅ | ✅ |
| Splunk | ✅ | ✅ | ✅ | ✅ | ✅ |
| Elasticsearch | ✅ | ✅ | ✅ | ✅ | ✅ |
| Syslog | ✅ | ✅ | ✅ | ✅ | ✅ |
| Windows EventLog | ✅ | ✅ | ❌ | ❌ | ❌* |

*Windows EventLog can run in Docker with Windows containers

---

**Version**: 1.0  
**Status**: Production Ready  
**Date**: 2026-02-27
