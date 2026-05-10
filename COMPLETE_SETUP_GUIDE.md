═══════════════════════════════════════════════════════════════════════════════
COMPLETE SETUP GUIDE - CONNECT ALL 7 CONNECTORS
═══════════════════════════════════════════════════════════════════════════════

Welcome! This guide will walk you through setting up all 7 connectors with real
infrastructure (or mock infrastructure if you don't have it yet).

═══════════════════════════════════════════════════════════════════════════════
QUICK START (5 MINUTES) - TEST WITH LOCALHOST
═══════════════════════════════════════════════════════════════════════════════

WHAT YOU GET:
  ✓ All 7 connectors configured and running
  ✓ Syslog listener working
  ✓ Error messages for connectors without real infrastructure (normal)
  ✓ Ready to send test events

STEP 1: Deploy connectors with localhost config

  PowerShell:
  
  $env:SPLUNK_HOST='localhost:8089'
  $env:KAFKA_BROKERS='localhost:9092'
  $env:ELASTIC_HOSTS='localhost:9200'
  $env:REST_API_URL='http://localhost:8443/v1/events'
  $env:WEBSOCKET_URL='wss://localhost:8443/stream'
  $env:SYSLOG_HOST='localhost'
  $env:SYSLOG_PORT='514'
  
  python run_connector_advanced.py 4

STEP 2: In another terminal, send test events

  python send_syslog.py localhost 514 10

That's it! You'll see:
  - Syslog events flowing through ✓
  - Error messages for missing endpoints (expected) ⚠
  - Ingestor processing events ✓

═══════════════════════════════════════════════════════════════════════════════
PRODUCTION SETUP - OPTION A: WITH DOCKER (RECOMMENDED)
═══════════════════════════════════════════════════════════════════════════════

Best for: Testing locally with real infrastructure components

PREREQUISITES:
  - Docker Desktop (https://www.docker.com/products/docker-desktop)
  - 8GB RAM available

STEP 1: Start Elasticsearch (in PowerShell)

  docker run -d --name elasticsearch -p 9200:9200 \\
    -e "discovery.type=single-node" \\
    -e "xpack.security.enabled=false" \\
    docker.elastic.co/elasticsearch/elasticsearch:7.15.0

  Wait 10 seconds for it to start
  Verify: curl http://localhost:9200
  You should see JSON response with version info

STEP 2: Start Kafka (in PowerShell)

  # Start Zookeeper first
  docker run -d --name zookeeper -p 2181:2181 \\
    -e ZOOKEEPER_CLIENT_PORT=2181 \\
    confluentinc/cp-zookeeper:latest
  
  # Then start Kafka
  docker run -d --name kafka -p 9092:9092 \\
    -e KAFKA_BROKER_ID=1 \\
    -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \\
    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \\
    -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \\
    confluentinc/cp-kafka:latest

  Wait 10 seconds for it to start
  Verify: docker ps (should show kafka and zookeeper)

STEP 3: Start Python mock servers (in new PowerShell)

  # This starts mock REST API, WebSocket, and Splunk
  python setup_infrastructure.py

  Keep this window open!

STEP 4: Deploy all 7 connectors (in new PowerShell)

  $env:SPLUNK_HOST='localhost:8089'
  $env:SPLUNK_USER='admin'
  $env:SPLUNK_PASSWORD='admin'
  $env:KAFKA_BROKERS='localhost:9092'
  $env:ELASTIC_HOSTS='localhost:9200'
  $env:REST_API_URL='http://localhost:8443/v1/events'
  $env:WEBSOCKET_URL='wss://localhost:8443/stream'
  
  python run_connector_advanced.py 4

STEP 5: Send test events (in new PowerShell)

  python send_syslog.py localhost 514 10

VERIFY:
  Terminal with connectors should show:
  ✓ [syslog] Event #1: WORKSTATION-01 | T1086
  ✓ [rest] Event #1: WORKSTATION-01 | T1071
  ✓ [websocket] Alert: "Suspicious PowerShell Execution"
  ... (events arriving from all 7 sources)

═══════════════════════════════════════════════════════════════════════════════
PRODUCTION SETUP - OPTION B: WITH YOUR ACTUAL INFRASTRUCTURE
═══════════════════════════════════════════════════════════════════════════════

Best for: Real security operations center integration

STEP 1: Gather your infrastructure details

  You need the hostnames/IPs for:
  ☐ Splunk instance (host:port, e.g., splunk.company.com:8089)
  ☐ Kafka brokers (host:port list, e.g., kafka1:9092,kafka2:9092)
  ☐ Elasticsearch cluster (host:port list, e.g., es1:9200,es2:9200)
  ☐ REST API endpoint (full URL, e.g., https://api.company.com/v1/events)
  ☐ WebSocket endpoint (wss URL, e.g., wss://alerts.company.com:8443/stream)
  ☐ Splunk credentials (username, password)

STEP 2: Set environment variables with your infrastructure

  PowerShell example (replace with YOUR details):
  
  $env:SPLUNK_HOST='splunk.company.com:8089'
  $env:SPLUNK_USER='siem_user'
  $env:SPLUNK_PASSWORD='SecurePassword123'
  $env:KAFKA_BROKERS='kafka1.company.com:9092,kafka2.company.com:9092'
  $env:ELASTIC_HOSTS='es1.company.com:9200,es2.company.com:9200'
  $env:REST_API_URL='https://security-api.company.com/v1/events'
  $env:WEBSOCKET_URL='wss://soc-alerts.company.com:8443/stream'
  $env:SYSLOG_HOST='syslog.company.com'
  $env:SYSLOG_PORT='514'

STEP 3: Deploy connectors

  python run_connector_advanced.py 4

STEP 4: Verify connectivity

  Check that you see status messages like:
  ✓ [splunk] Connected! Processing events...
  ✓ [rest] Polling https://security-api.company.com...
  ✓ [syslog] Listening on 0.0.0.0:514
  ✓ [elasticsearch] Connected to cluster

STEP 5: Monitor events flowing in

  Watch the connector output as your infrastructure sends events.
  Intelligence reports will be generated automatically.

═══════════════════════════════════════════════════════════════════════════════
PRODUCTION SETUP - OPTION C: PYTHON MOCK INFRASTRUCTURE ONLY
═══════════════════════════════════════════════════════════════════════════════

Best for: Testing when you don't have Docker or real infrastructure yet

STEP 1: Start mock infrastructure (in PowerShell)

  python setup_infrastructure.py

  This starts:
  - Mock REST API Server
  - Mock WebSocket Server
  - Mock Splunk Simulator
  
  Keep this window open!

STEP 2: In new PowerShell, deploy connectors

  $env:SPLUNK_HOST='localhost:8089'
  $env:SPLUNK_USER='admin'
  $env:SPLUNK_PASSWORD='admin'
  $env:REST_API_URL='http://localhost:8443/v1/events'
  $env:WEBSOCKET_URL='wss://localhost:8443/stream'
  $env:KAFKA_BROKERS='localhost:9092'
  $env:ELASTIC_HOSTS='localhost:9200'
  
  python run_connector_advanced.py 4

STEP 3: In another PowerShell, send test events

  python send_syslog.py localhost 514 20

VERIFY:
  Events will appear from:
  ✓ Syslog (your test events)
  ✓ Mock REST API (configured events)
  ✓ Mock WebSocket (simulated alerts)
  ✓ Mock Splunk (security events)

═══════════════════════════════════════════════════════════════════════════════
WHAT EACH CONNECTOR DOES
═══════════════════════════════════════════════════════════════════════════════

1. SPLUNK CONNECTOR
   - Pulls security events from Splunk instance
   - Uses saved search queries
   - Endpoint: SPLUNK_HOST (host:port)
   - Credentials: SPLUNK_USER, SPLUNK_PASSWORD

2. KAFKA CONNECTOR
   - Subscribes to security-events topic
   - Consumes real-time message stream
   - Endpoint: KAFKA_BROKERS (comma-separated list)
   - Speed: 10,000-100,000 events/sec

3. ELASTICSEARCH CONNECTOR
   - Queries security indices
   - Uses scroll API for streaming
   - Endpoint: ELASTIC_HOSTS (comma-separated list)
   - Speed: 1,000-10,000 events/sec

4. SYSLOG CONNECTOR
   - Listens on port 514 (UDP/TCP)
   - Receives RFC 3164 syslog messages
   - Endpoint: SYSLOG_HOST:SYSLOG_PORT
   - Speed: 1,000-10,000 events/sec
   - NO EXTERNAL DEPENDENCIES - always works!

5. REST API CONNECTOR
   - Polls HTTP endpoint every 10 seconds
   - Expects JSON event responses
   - Endpoint: REST_API_URL (full URL)
   - Speed: 100-1,000 events/sec
   - Useful for cloud security APIs (AWS, Azure, etc.)

6. WEBSOCKET CONNECTOR
   - Maintains persistent WebSocket connection
   - Receives real-time alert streams
   - Endpoint: WEBSOCKET_URL (wss:// URL)
   - Speed: 1,000-10,000 events/sec
   - Auto-reconnects on disconnect

7. WINDOWS EVENT LOG CONNECTOR
   - Reads local Security event log
   - Monitors for real-time events
   - No external endpoint needed!
   - Speed: 100-1,000 events/sec
   - Requires: Administrative privileges

═══════════════════════════════════════════════════════════════════════════════
CONNECTOR STATUS MEANINGS
═══════════════════════════════════════════════════════════════════════════════

RUNNING (0 errors):
  ✓ Connector is active and processing/listening for events
  ✓ No configuration issues detected

RUNNING (with errors):
  ⚠ Connector is running but encountered transient errors
  ⚠ Retrying connection with exponential backoff
  ⚠ Will succeed once endpoint becomes available

COMPLETED (1+ errors):
  ✗ Connector tried and failed
  ✗ Stopping due to configuration error or unavailable endpoint
  ✗ Check endpoint URL and credentials

═══════════════════════════════════════════════════════════════════════════════
EXPECTED OUTPUT IN STEP 4/5
═══════════════════════════════════════════════════════════════════════════════

After deploying connectors and sending test events, you should see:

[+] Scenario: Modern SOC (All Connectors)
[+] Running 7 connector(s)...

[splunk] Starting...
[splunk] Connected! Processing events...
[splunk] Event #1: WORKSTATION-01 | ProcessCreate | T1086 | 2026-02-27T10:15:30Z
[splunk] Event #2: WORKSTATION-01 | NetworkConnection | T1071 | 2026-02-27T10:15:31Z

[rest] Starting...
[REST API] Starting poll from http://localhost:8443/v1/events...
[rest] Event #1: WORKSTATION-01 | FileCreate | T1547 | 2026-02-27T10:15:32Z

[websocket] Starting...
[WebSocket] Connecting to wss://localhost:8443/stream...
[websocket] Alert: Suspicious PowerShell Execution Detected

[syslog] Starting...
[Syslog] Listening on 0.0.0.0:514
[syslog] Event #1: WORKSTATION-01 | ProcessCreate | T1059 | 2026-02-27T10:15:30Z
[syslog] Event #2: WORKSTATION-01 | NetworkConnection | T1071 | 2026-02-27T10:15:31Z
... (10 events from test sender)
[syslog] Batch #1 processed: 10 events in 0.5 seconds

[kafka] Starting...
[kafka] Connected to brokers ['localhost:9092']
[kafka] Event #1: WORKSTATION-02 | DNSQuery | T1071 | 2026-02-27T10:15:34Z

[elastic] Starting...
[elasticsearch] Connected to ['localhost:9200']
[elastic] Event #1: DOMAIN-CONTROLLER | LogonEvent | T1078 | 2026-02-27T10:15:35Z

[windows_eventlog] Starting...
[Windows EventLog] Monitoring Security log
[windows_eventlog] Event #1: WORKSTATION-03 | PrivilegeElevation | T1134 | ...

════════════════════════════════════════════════
FINAL REPORT
════════════════════════════════════════════════
Connector          | Events   | Errors | Status
────────────────────────────────────────────────
splunk             | 2        | 0      | Running
kafka              | 1        | 0      | Running
elastic            | 1        | 0      | Running
websocket          | 1        | 0      | Running
rest               | 1        | 0      | Running
syslog             | 10       | 0      | Running
windows_eventlog   | 1        | 0      | Running
────────────────────────────────────────────────
TOTAL EVENTS INGESTED: 17
THROUGHPUT: 34 events/sec
STATUS: ✓ ALL CONNECTORS ACTIVE

═══════════════════════════════════════════════════════════════════════════════
TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

Q: I see "Connection refused" errors
A: The endpoint doesn't exist or is not running
   - Check that you started infrastructure (Docker/mock servers)
   - Verify hostnames are correct and accessible
   - Check ports are correct (8089 for Splunk, 9092 for Kafka, etc.)

Q: Syslog events not appearing
A: Check if syslog connector started
   - Should see "[Syslog] Listening on 0.0.0.0:514"
   - Make sure port 514 is not in use (try 5514 instead)
   - Update SYSLOG_PORT if using different port

Q: REST API showing request failures
A: Check the REST API endpoint
   - Verify URL is correct and server is running
   - Check that endpoint returns valid JSON
   - Verify authentication/headers if needed

Q: Windows Event Log permission denied
A: Run PowerShell as Administrator
   - Right-click PowerShell, "Run as administrator"
   - Try again
   - Or ignore - Windows Event Log is optional

Q: Kafka/Elasticsearch not connecting
A: Have you started Docker containers?
   - docker ps should show kafka and elasticsearch
   - Check network connectivity to Docker containers
   - Verify ports (9092 for Kafka, 9200 for Elasticsearch)

Q: Memory/resource errors
A: Reduce batch size:
   - Edit ingestion/realtime_ingestor.py
   - Change batch_size = 10 to batch_size = 5
   - Or increase system RAM

═══════════════════════════════════════════════════════════════════════════════
WHAT'S NEXT?
═══════════════════════════════════════════════════════════════════════════════

1. ✓ Deployed all 7 connectors
2. ✓ Configured with real/mock infrastructure
3. ✓ Verified events flowing through

Now:
4. Monitor intelligence reports: reporting/intelligence_report.json
5. Check threat scores and campaign classifications
6. Set up alerting on threat detection
7. Scale to production infrastructure
8. Integrate with your existing SIEM

For production deployment:
- Run in containerized environment (Docker/Kubernetes)
- Use persistent storage for reports
- Set up monitoring and alerting
- Configure backup/redundancy
- Tune batch sizes for throughput
- Add authentication/authorization

═══════════════════════════════════════════════════════════════════════════════

Questions? Check ENDPOINTS_EXPLAINED.md for details on what each endpoint does.

Ready to deploy? Start with Option A (Quick Start), then upgrade to Option B
(Docker) or Option C (Your Infrastructure) when ready!

═══════════════════════════════════════════════════════════════════════════════
