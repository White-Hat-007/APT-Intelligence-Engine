================================================================================
  WHAT DOES "1ST" MEAN? - COMPLETE EXPLANATION
================================================================================

When you see the connectors output, here's what each part means:

## THE FLOW: Data Source → Connector → Engine → Intelligence

```
Real Data Sources (Splunk, Kafka, etc.)
            ↓
        Connectors (read events in real-time)
            ↓
    Real-Time Ingestor (batches events)
            ↓
    Analytics Engine (clustering, correlation)
            ↓
Intelligence Reports (final output)
```

## WHAT EACH CONNECTOR DOES

┌─────────────────┬──────────────────┬─────────────────────────────────────────┐
│ Connector       │ Data Source      │ Real-World Use                          │
├─────────────────┼──────────────────┼─────────────────────────────────────────┤
│ Kafka           │ Message Broker   │ Streaming events from millions of       │
│                 │                  │ sources in real-time (10k-100k evt/s)   │
│                 │                  │                                         │
│ Splunk          │ SIEM Platform    │ Ingesting logs from Windows/Linux       │
│                 │                  │ endpoints stored in Splunk (100-1k evt/s)
│                 │                  │                                         │
│ Elasticsearch   │ Search Engine    │ Reading from ELK Stack analyzing        │
│                 │                  │ application and infrastructure logs      │
│                 │                  │ (1k-10k evt/s)                         │
│                 │                  │                                         │
│ Syslog          │ Legacy Protocol  │ Listening for RFC 3164 events from      │
│                 │                  │ firewalls, routers, network devices     │
│                 │                  │ (1k-10k evt/s)                         │
│                 │                  │                                         │
│ REST API        │ HTTP Endpoint    │ Polling custom API for security events  │
│                 │                  │ with bearer token authentication         │
│                 │                  │ (100-1k evt/s)                         │
│                 │                  │                                         │
│ WebSocket       │ Real-time Stream │ Connecting to live event feeds pushing  │
│                 │                  │ data as it happens (1k-10k evt/s)      │
│                 │                  │                                         │
│ Windows Log     │ Native OS        │ Reading Security/System Event Log from  │
│                 │                  │ Windows endpoints directly (100-1k evt/s)
└─────────────────┴──────────────────┴─────────────────────────────────────────┘

## WHAT "1ST" MEANS IN THE CONTEXT

If you see a message like:
"[splunk] Event #1: hostname | T1059 | 2026-02-27T10:15:30Z"

BREAKDOWN:
- [splunk]        = This is from the Splunk connector
- Event #1        = First event processed from this source
- hostname        = The system where the attack technique was detected
- T1059           = MITRE ATT&CK technique (Command Line Interface execution)
- timestamp       = When the event occurred

## WHAT A REAL ENDPOINT LOOKS LIKE

### Splunk Endpoint Example:
```
Host: splunk.mycompany.local
Port: 8089
Username: apt_detector
Password: secure_password
Search Query: Find all Sysmon events with process creation
```
This tells the connector WHERE to find Splunk, HOW to authenticate, and WHAT to search for.

### Kafka Endpoint Example:
```
Bootstrap Servers: kafka1.cloud:9092, kafka2.cloud:9092
Topic: security.events.raw
Group ID: apt_threat_intelligence
```
This tells the connector WHICH Kafka brokers to connect to and WHICH TOPIC to consume.

### Syslog Endpoint Example:
```
Listen Address: 0.0.0.0 (all interfaces)
Listen Port: 514 (standard syslog)
Protocol: UDP (or TCP)
```
This tells the connector WHICH INTERFACE to listen on for incoming syslog events.

## THE 5 INFRASTRUCTURE SCENARIOS

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO 1: Enterprise Splunk + Syslog (Most Common)                         │
├──────────────────────────────────────────────────────────────────────────────┤
│ Who Uses This:                                                               │
│   - Large enterprises with existing Splunk investment                        │
│   - Organizations with diverse devices (firewalls, network equipment)        │
│                                                                              │
│ Data Flow:                                                                   │
│   Windows/Linux Endpoints → Splunk Forwarders → Splunk Enterprise            │
│   Network Devices → Syslog → Syslog Aggregator                              │
│   Both → Your APT Intelligence Engine                                       │
│                                                                              │
│ Configuration:                                                               │
│   SPLUNK_HOST=splunk.mycompany.local:8089                                   │
│   SPLUNK_USER=apt_detector                                                  │
│   SPLUNK_PASSWORD=your_secure_password                                      │
│   SYSLOG_PORT=514                                                           │
│                                                                              │
│ Network Requirements:                                                        │
│   ✓ Network access to Splunk on port 8089 (API)                            │
│   ✓ Network access to Syslog server on port 514                            │
│   ✓ Outbound HTTPS if using SSL                                            │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO 2: Cloud-Native (Kafka + Elasticsearch)                            │
├──────────────────────────────────────────────────────────────────────────────┤
│ Who Uses This:                                                               │
│   - Cloud-first organizations (AWS, Azure, GCP)                             │
│   - Container and microservices environments                                │
│   - Enterprises running ELK Stack                                           │
│                                                                              │
│ Data Flow:                                                                   │
│   Containers/Kubernetes → Kafka Brokers → Topic                             │
│   Application Logs → Filebeat → Elasticsearch                               │
│   Both topics → Your APT Intelligence Engine                                │
│                                                                              │
│ Configuration:                                                               │
│   KAFKA_BROKERS=kafka1.cloud:9092,kafka2.cloud:9092                        │
│   KAFKA_TOPIC=security.events.raw                                          │
│   ELASTIC_HOSTS=es1.cloud:9200,es2.cloud:9200                              │
│                                                                              │
│ Network Requirements:                                                        │
│   ✓ Network access to Kafka brokers on port 9092                           │
│   ✓ Network access to Elasticsearch cluster on port 9200                    │
│   ✓ Outbound to cloud services if on-prem engine                           │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO 3: Hybrid (Splunk + Kafka + REST API)                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ Who Uses This:                                                               │
│   - Enterprises transitioning to cloud                                      │
│   - Organizations with multiple SIEM investments                            │
│   - Companies with custom security APIs                                     │
│                                                                              │
│ Data Flow:                                                                   │
│   Legacy Systems → Splunk Enterprise                                        │
│   Cloud Systems → Kafka Cluster                                             │
│   Custom Apps → REST API Endpoint                                           │
│   All three → Your APT Intelligence Engine (unified analysis)               │
│                                                                              │
│ Configuration:                                                               │
│   (Combination of Scenario 1 + 2 + custom API credentials)                 │
│                                                                              │
│ Power Of This: Correlate attacks across EVERYTHING!                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO 4: Modern SOC (All 7 Connectors)                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Who Uses This:                                                               │
│   - Large Security Operations Centers                                       │
│   - Organizations requiring multi-source correlation                        │
│   - Advanced persistent threat hunters                                      │
│                                                                              │
│ Data Flow (Multi-Source Correlation):                                       │
│   Splunk (Windows logs) ┐                                                    │
│   Kafka (App events) ──┼→ Real-Time Ingestor → Analytics → Reports          │
│   Elasticsearch (Cloud)┼→                                                    │
│   Syslog (Network) ───┤                                                      │
│   WebSocket (Alerts) ──┘                                                     │
│                                                                              │
│ Example Attack Chain Detection:                                              │
│   1. Process creation (Splunk)                                              │
│   2. Network connection (Kafka)                                             │
│   3. File write (Elasticsearch)                                             │
│   4. Network flow (Syslog)                                                  │
│   All correlated within seconds → APT detected!                             │
│                                                                              │
│ Configuration:                                                               │
│   Use SCENARIO_SOC configuration                                            │
│   (Includes all components)                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO 5: Lightweight (Syslog Only - No External Dependencies)            │
├──────────────────────────────────────────────────────────────────────────────┤
│ Who Uses This:                                                               │
│   - Organizations evaluating the platform                                   │
│   - Quick deployments without dependencies                                  │
│   - Development/testing environments                                        │
│                                                                              │
│ Data Flow:                                                                   │
│   Any Syslog Source → Listens on 0.0.0.0:514 → Your APT Engine             │
│                                                                              │
│ Configuration:                                                               │
│   SYSLOG_PORT=514                                                           │
│   (Everything built with Python stdlib, no pip installs!)                   │
│                                                                              │
│ Usage: Perfect for testing before full deployment                           │
└──────────────────────────────────────────────────────────────────────────────┘

## HOW TO USE THE ADVANCED RUNNER

### Option 1: Interactive Menu
```bash
python run_connector_advanced.py
```
This launches an interactive menu where you:
1. Select your infrastructure scenario
2. Choose which connectors to run
3. Watch real-time events being processed

### Option 2: Command-Line (Fastest)
```bash
# Run scenario 1 (Enterprise) with all connectors
python run_connector_advanced.py 1

# Run scenario 2 (Cloud) with only Kafka
python run_connector_advanced.py 2 kafka

# Run scenario 4 (Modern SOC) with multiple connectors
python run_connector_advanced.py 4 splunk kafka elastic

# Run scenario 5 (Lightweight) - ready to go!
python run_connector_advanced.py 5
```

### Option 3: Environment Variables (Production)
```bash
# Override default endpoints with your infrastructure
export SPLUNK_HOST=your-splunk-server.com:8089
export SPLUNK_USER=apt_detector
export SPLUNK_PASSWORD=your_secure_password
export KAFKA_BROKERS=broker1.local:9092,broker2.local:9092
export KAFKA_TOPIC=security.raw

python run_connector_advanced.py 3  # Runs Hybrid scenario with YOUR infrastructure
```

## REALISTIC EXAMPLE: Running Against Real Splunk

1. You have Splunk running at: splunk.company.local:8089
2. Your events are in: sourcetype=sysmon, sourcetype=windows_security
3. You want to detect: Process creation, network connections, file writes

```bash
# Set your Splunk credentials
export SPLUNK_HOST=splunk.company.local:8089
export SPLUNK_USER=apt_detector
export SPLUNK_PASSWORD=SecurePassword123!

# Run the Splunk connector
python run_connector_advanced.py 1 splunk

# OUTPUT:
# [+] Scenario: Enterprise Splunk + Syslog
# [+] Running 1 connector(s)...
# [+] Launching splunk...
# [splunk] Starting...
# [splunk] Connected to Splunk!
# [splunk] Event #1: W2K19-SQL | T1059 | 2026-02-27T10:15:30Z
# [splunk] Event #11: W2K19-APP | T1087 | 2026-02-27T10:15:35Z
# ...
```

## UNDERSTANDING THE ERROR MESSAGES

```
[splunk] Error: ImportError
```
Means: You need to install splunk-sdk
Fix: pip install splunk-sdk

```
[kafka] Error: NoBrokersAvailable
```
Means: Kafka endpoints aren't reachable
Fix: Check KAFKA_BROKERS environment variable and network connectivity

```
[rest] Error: NameResolutionError
```
Means: API endpoint hostname doesn't resolve
Fix: Check REST_API_URL and DNS/network

```
[windows_eventlog] Error: (1314, 'OpenEventLogW', 'privilege is not held')
```
Means: Running without admin privileges
Fix: Run Python as Administrator or use different event log

## PRODUCTION DEPLOYMENT CHECKLIST

□ Choose your scenario (1-5)
□ Get actual endpoint details from your infrastructure team
□ Set secure credentials in environment variables (NOT in code!)
□ Test connectivity: telnet/curl to each endpoint
□ Verify credentials have required permissions
□ Run lightweight scenario first (scenario 5 - syslog)
□ Gradually add more connectors
□ Monitor logs for errors
□ Tune batch_size and time_window for your throughput
□ Set up alerting on intelligence reports

================================================================================

Ready to configure? Let me know which scenario matches your infrastructure!

