# Real-Time Ingestion - Quick Start Guide

## Operating Modes

### Batch Simulation
```python
MODE = "simulate"  # 3 synthetic APT campaigns
python main.py
```

### Batch Sysmon Ingestion
```python
MODE = "sysmon"    # Static JSON log file
python main.py
```

### Real-Time Streaming ⭐ (NEW)
```python
MODE = "realtime"  # Continuous event ingestion
python main.py
```

---

## Configuration

Edit `main.py` to adjust real-time parameters:

```python
# Batch size trigger (events)
REALTIME_BATCH_SIZE = 10

# Time window trigger (seconds)
REALTIME_TIME_WINDOW = 3.0

# Total runtime (seconds)
REALTIME_DURATION = 30
```

**Behavior**:
- Batch triggers when **size is reached OR time window expires** (whichever first)
- After each batch: events are mapped to MITRE tactics → fingerprints generated
- After streaming completes: fingerprints are aggregated and clustered

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│  Event Source                       │  (Generator)
│  • create_simulated_event_stream()  │
│  • [Future] Kafka, WebSocket, REST  │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  RealTimeIngestor                   │  (Thread-Safe)
│  • Ingestor Thread (pulls events)   │
│  • Processor Thread (batches)       │
│  • Queue + Batch Buffer             │
│  • Callbacks: on_batch_ready()      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  RealtimeAnalyticsContext           │  (State Machine)
│  • on_batch_ready(events)           │
│    ├─ map_to_tactics()              │
│    ├─ generate_fingerprint()        │
│    └─ accumulate fingerprint        │
│  • aggregate_fingerprints()         │
│  • get_summary()                    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  Existing Analytics Pipeline        │
│  • cluster_campaigns()              │
│  • compute_similarity()             │
│  • generate_report()                │
└─────────────────────────────────────┘
```

---

## Key Classes

### RealTimeIngestor

**Initialization**:
```python
ingestor = RealTimeIngestor(
    batch_size=10,
    time_window_seconds=3.0,
    max_queue_size=500
)
```

**Set Event Source**:
```python
event_source = create_simulated_event_stream(
    campaign_id="CAMPAIGN-001",
    num_events=100,
    delay_seconds=0.05
)
ingestor.set_event_source(event_source)
```

**Register Callbacks**:
```python
def on_batch_ready(batch_events):
    print(f"Batch ready: {len(batch_events)} events")

ingestor.register_batch_callback(on_batch_ready)
```

**Control**:
```python
ingestor.start()           # Launch threads
stats = ingestor.get_stats()  # Get metrics
ingestor.stop()            # Graceful shutdown
```

### RealtimeAnalyticsContext

**Initialization**:
```python
ctx = RealtimeAnalyticsContext()
```

**Callback Integration**:
```python
ingestor.register_batch_callback(ctx.on_batch_ready)
```

**Results**:
```python
summary = ctx.get_summary()
# {
#   "total_events": 150,
#   "total_batches": 15,
#   "aggregated_fingerprint": {...}
# }
```

---

## Event Flow Example

```
Time  Event Source           Ingestor Queue     Processor Batch       Callback
────  ───────────────        ──────────────     ───────────────       ────────
0.0s  Event 1 → Queue
0.05s Event 2 → Queue
0.1s  Event 3 → Queue
      ...
0.5s  Event 10 → Queue      [10 events]        [FULL] → Process batch
                                                 ↓
                                              map_to_tactics()
                                              generate_fingerprint()
                                              → on_batch_ready()
                                              ↓
                                              Batch #1 printed
      Event 11 → Queue                        Clear buffer
      ...
3.0s  [Time window expires]
      Even if < 10 events    [7 events]        [TIME] → Process batch
                                                 ↓
                                              Batch #2 processed
```

---

## Integration with Existing Modules

All existing modules work **unchanged**:

```python
from ingestion.simulator import simulate_campaign
from ingestion.sysmon_parser import parse_sysmon_log
from mapping.mitre_mapper import map_to_tactics
from analytics.fingerprint_engine import generate_fingerprint
from analytics.clustering_engine import cluster_campaigns
from analytics.similarity_engine import compute_similarity
from reporting.intelligence_report import generate_report
```

**In real-time mode**, these are called within `RealtimeAnalyticsContext.on_batch_ready()`:
1. `map_to_tactics(batch_events)` → Add tactical classifications
2. `generate_fingerprint(mapped_events)` → Behavioral vector
3. Store fingerprint for later clustering
4. After streaming: `cluster_campaigns(all_fingerprints)` → Group similar batches
5. `generate_report(aggregated_fingerprint)` → Intelligence summary

---

## Thread Safety Guarantees

✅ **Event Queue**: Python's `queue.Queue` is internally synchronized  
✅ **Batch Buffer**: Protected by `threading.Lock`  
✅ **Statistics**: All counts protected by lock  
✅ **Callbacks**: Invoked outside lock (no deadlock risk)  
✅ **Shutdown**: Coordinated via `threading.Event`  

**No data races, no synchronization bugs.**

---

## Statistics API

Check ingestion health in real-time:

```python
stats = ingestor.get_stats()
print(stats)
# {
#   "total_events_ingested": 150,
#   "total_batches_processed": 15,
#   "current_buffer_size": 3,       # Waiting for next batch
#   "queue_size": 0,                # Events pending move to batch
#   "batch_size_config": 10,
#   "time_window_config": 3.0
# }
```

---

## Example: Custom Event Source

```python
def my_event_source():
    """Custom generator yielding events."""
    for i in range(100):
        yield {
            "campaign_id": "CUSTOM-001",
            "event_id": str(uuid.uuid4()),
            "timestamp": str(datetime.now(timezone.utc)),
            "host": f"HOST-{i % 5}",
            "technique_id": random.choice(["T1059", "T1003", "T1021"]),
            "source": "custom"
        }
        time.sleep(0.01)  # Simulated delay

# Use it
ingestor.set_event_source(my_event_source())
ingestor.start()
```

---

## Output Example

```
========== REALTIME INGESTION PIPELINE ==========
Campaign: REALTIME-CAMPAIGN-001
Batch Size: 10 events
Time Window: 3.0s
Duration: 30s

[RealTimeIngestor] Started (ingestor and processor threads)

[REALTIME] Batch #1 processed (10 events)
  Techniques: ['T1003', 'T1041', 'T1059', 'T1021', 'T1547']
  Hosts: ['HOST-4', 'HOST-5', 'HOST-1', 'HOST-3', 'HOST-2']
  Complexity: 25

[STATS] Events: 19, Batches: 1, Queue: 0

[REALTIME] Batch #2 processed (10 events)
  Techniques: ['T1003', 'T1041', 'T1059']
  Hosts: ['HOST-4', 'HOST-1', 'HOST-5']
  Complexity: 15

...

========== REALTIME ANALYSIS SUMMARY ==========
Total Events Processed: 150
Total Batches: 15

========== INTELLIGENCE REPORT ==========
Cluster Classification: 0
Risk Level: High
Technique Distribution: {'T1003': 14, 'T1041': 14, 'T1059': 14, ...}
Affected Hosts: ['HOST-1', 'HOST-2', 'HOST-3', 'HOST-4', 'HOST-5']
Behavioral Complexity Score: 25

========== REALTIME CLUSTERING ANALYSIS ==========
Batch #1 → Cluster 0
Batch #2 → Cluster 0
Batch #3 → Cluster 1
...
Batch #15 → Cluster 0

========== Analysis Complete ==========
```

---

## Troubleshooting

### Issue: Batches not processing
**Check**: Is event source yielding events?
```python
ingestor.get_stats()  # Check total_events_ingested
```

### Issue: High queue depth
**Action**: Increase `batch_size` or decrease `delay_seconds` in event source

### Issue: Shutdown takes >5s
**Reason**: Event source generator not stopping  
**Fix**: Add timeout to generator or ensure it's finite

### Issue: Memory growing
**Check**: Batch fingerprints accumulating?
```python
ctx.batch_fingerprints  # Should be ~15 items for 30s run
```

---

## Future: Kafka Integration (Planned)

```python
# Mock - implement when Kafka client available
def kafka_event_stream(topic, bootstrap_servers):
    from kafka import KafkaConsumer
    consumer = KafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    for msg in consumer:
        yield json.loads(msg.value)

# Usage
ingestor.set_event_source(
    kafka_event_stream(topic="security_events", bootstrap_servers=["localhost:9092"])
)
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `ingestion/realtime_ingestor.py` | Core ingestor class and helpers |
| `main.py` | Orchestra mode, analytics context |
| `REALTIME_ARCHITECTURE.md` | Detailed design document |
| `REALTIME_QUICKSTART.md` | This file |

---

## Testing Commands

```bash
# Run realtime pipeline (30 seconds)
python main.py

# Switch to simulate
# Edit main.py: MODE = "simulate"
python main.py

# Switch to sysmon
# Edit main.py: MODE = "sysmon"
python main.py
```

---

**Version**: 1.0  
**Status**: Production-Ready  
**Date**: 2026-02-27
