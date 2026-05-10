================================================================================
  PRODUCTION DEPLOYMENT GUIDE - ALL 7 CONNECTORS
================================================================================

This guide shows how to configure each connector with realistic values from
actual deployments. Use these as templates for YOUR infrastructure.

================================================================================
1. SPLUNK CONNECTOR - Enterprise SIEM Integration
================================================================================

WHAT IT DOES:
  Connects to Splunk Enterprise and retrieves events matching your search query.
  Useful for ingesting process creation, network connection, and file write
  events from Windows and Linux endpoints.

REQUIREMENTS:
  ✓ Splunk Enterprise running (version 7.0+)
  ✓ Network access to Splunk management port (default 8089)
  ✓ API user with 'search' capability
  ✓ pip install splunk-sdk

CONFIGURATION TEMPLATE:
```python
{
    "splunk": {
        "host": "splunk-indexer.company.local:8089",
        "username": "api_user",
        "password": "secure_password_here",  # Use env var in production!
        "search_query": """
            (sourcetype=sysmon OR sourcetype=windows_security OR sourcetype=linux_audit)
            (EventCode=1 OR EventCode=3 OR EventCode=5 OR EventCode=11 OR 
             EventCode=21 OR EventCode=23)
            earliest=-10m latest=now
        """
    }
}
```

REAL-WORLD EXAMPLE:
```bash
export SPLUNK_HOST=splunk-prod.internal.com:8089
export SPLUNK_USER=threat_intel_user
export SPLUNK_PASSWORD=$(cat /secure/splunk_password.txt)

python run_connector_advanced.py 1 splunk
```

TROUBLESHOOTING:
  Error: "HTTP 401 Unauthorized"
    → Username/password incorrect, verify permissions
  
  Error: "Connection timed out"
    → Splunk host unreachable, check firewall and network

PERFORMANCE:
  - Typical throughput: 100-1000 events/sec
  - Latency: 2-5 seconds from event in Splunk to ingestion
  - Depends on search complexity and Splunk cluster size

================================================================================
2. KAFKA CONNECTOR - High-Speed Message Streaming
================================================================================

WHAT IT DOES:
  Connects to Apache Kafka cluster and consumes events from a topic.
  Used for high-throughput streaming of security events from modern infrastructure.

REQUIREMENTS:
  ✓ Kafka cluster running (version 2.0+)
  ✓ Network access to broker ports (typically 9092)
  ✓ Topic created with events available
  ✓ pip install kafka-python

CONFIGURATION TEMPLATE:
```python
{
    "kafka": {
        "bootstrap_servers": [
            "kafka-broker-1.cloud.local:9092",
            "kafka-broker-2.cloud.local:9092",
            "kafka-broker-3.cloud.local:9092"
        ],
        "topic": "security.events.raw",
        "group_id": "apt_threat_intelligence",
        "auto_offset_reset": "latest"
    }
}
```

REAL-WORLD EXAMPLE:
```bash
export KAFKA_BROKERS=kafka1.aws.local:9092,kafka2.aws.local:9092,kafka3.aws.local:9092
export KAFKA_TOPIC=prod-security-events

# Using environment variables
python run_connector_advanced.py 2 kafka
```

WHAT YOU NEED TO KNOW:
  - Each broker: hostname:port
  - Topic name: where your events are published
  - Group ID: identifies your consumer group
  - auto_offset_reset: start from "latest" (new events only) or "earliest" (all)

TROUBLESHOOTING:
  Error: "NoBrokersAvailable"
    → Brokers unreachable, test with: telnet kafka-broker-1.local 9092
  
  Error: "Unknown topic"
    → Topic doesn't exist, verify with: kafka-topics.sh --list

PERFORMANCE:
  - Typical throughput: 10,000-100,000 events/sec
  - Latency: <100ms from publication to ingestion
  - Highly scalable, event order preserved in partition

================================================================================
3. ELASTICSEARCH CONNECTOR - Search & Analytics
================================================================================

WHAT IT DOES:
  Connects to Elasticsearch cluster and scrolls through index matching your query.
  Great for ELK Stack environments with diverse log sources.

REQUIREMENTS:
  ✓ Elasticsearch cluster running
  ✓ Network access to REST endpoint (typically 9200)
  ✓ Index with events available
  ✓ Optional: credentials if X-Pack security enabled
  ✓ pip install elasticsearch

CONFIGURATION TEMPLATE:
```python
{
    "elastic": {
        "hosts": [
            "es-node-1.cluster.local:9200",
            "es-node-2.cluster.local:9200",
            "es-node-3.cluster.local:9200"
        ],
        "index_pattern": "logs-sysmon-*,logs-windows-*",
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": "now-1h",
                                "lte": "now"
                            }
                        }
                    },
                    {
                        "terms": {
                            "event.category": [
                                "process",
                                "file",
                                "network"
                            ]
                        }
                    }
                ]
            }
        }
    }
}
```

REAL-WORLD EXAMPLE:
```bash
export ELASTIC_HOSTS=elasticsearch1.local:9200,elasticsearch2.local:9200
python run_connector_advanced.py 2 elastic
```

FOR AUTHENTICATED ELASTICSEARCH:
```python
{
    "elastic": {
        "hosts": ["elastic.cluster.local:9200"],
        "basic_auth": ("elastic_user", "elastic_password"),
        "use_ssl": True,
        "verify_certs": False,  # Only if using self-signed certs
        "index_pattern": "logs-*",
        "query": {"match_all": {}}
    }
}
```

TROUBLESHOOTING:
  Error: "Connection refused"
    → Elasticsearch not running or port blocked
  
  Error: "401 Unauthorized"
    → Credentials incorrect, check X-Pack settings

PERFORMANCE:
  - Typical throughput: 1,000-10,000 events/sec
  - Latency: 1-3 seconds
  - Scroll size determines batch efficiency

================================================================================
4. SYSLOG CONNECTOR - RFC 3164 Protocol Listener
================================================================================

WHAT IT DOES:
  Listens for incoming syslog messages on a network socket.
  Standard protocol used by network devices, firewalls, routers, and servers.

REQUIREMENTS:
  ✓ Nothing! Uses Python stdlib only
  ✓ Port 514 available (or choose custom port)
  ✓ TCP or UDP (UDP is standard for low-latency networks)

CONFIGURATION TEMPLATE:
```python
{
    "syslog": {
        "host": "0.0.0.0",          # Listen on all interfaces
        "port": 514,                # Standard syslog port
        "protocol": "udp"           # or "tcp" for reliability
    }
}
```

REAL-WORLD DEPLOYMENT:
```bash
# Send syslog events to your machine on port 514
# From any device (firewall, router, Linux server, etc.):
#   logger -h YOUR_IP -n YOUR_MACHINE -P 514 "Test message"

python run_connector_advanced.py 5  # Lightweight scenario
```

WHAT IT RECEIVES:
```
<34>Feb 27 10:15:30 FIREWALL-01 access: Allow TCP 192.168.1.100:55123 -> 8.8.8.8:443
<166>Feb 27 10:15:31 ROUTER-02 BGP[12345]: Adjacency to 10.0.0.1 lost
<134>Feb 27 10:15:32 WEB-SERVER crash: Web service restarted unexpectedly
```

PARSE FACILITY CODES:
  0 = kernel (emergencies)
  1 = user-level (alerts)
  4 = security/authorization (warnings)
  16 = local0 (info)
  17 = local1 (notice)
  23 = local7 (debug)

CONFIGURING DEVICES TO SEND SYSLOG:
  Linux Server:
    echo "*.* @your_server_ip" >> /etc/rsyslog.conf
  
  Cisco Router:
    logging host your_server_ip
  
  Windows (with Winlogbeat):
    filebeat.yml configured to send to syslog server
  
  F5 Load Balancer:
    System > Event Processing > Logging Configuration

TROUBLESHOOTING:
  Messages not arriving?
    → Check firewall rules allow traffic on port 514
    → Verify syslog is listening: netstat -an | grep 514
  
  Parsing errors?
    → Some devices send non-standard formats, check raw messages

PERFORMANCE:
  - Typical throughput: 1,000-10,000 events/sec
  - Latency: <100ms
  - Lightweight, CPU efficient, no dependencies

BEST FOR:
  ✓ Network devices (firewalls, routers, switches)
  ✓ Legacy systems
  ✓ Distributed deployments
  ✓ Quick evaluation

================================================================================
5. REST API CONNECTOR - HTTP Polling
================================================================================

WHAT IT DOES:
  Polls a REST API endpoint at regular intervals and fetches JSON events.
  Useful for custom APIs or SIEM/SOC platforms that expose REST interfaces.

REQUIREMENTS:
  ✓ HTTP/HTTPS endpoint returning JSON
  ✓ Bearer token or basic auth (optional)
  ✓ pip install requests

CONFIGURATION TEMPLATE:
```python
{
    "rest": {
        "api_url": "https://api.siem.company.com/v1/events",
        "poll_interval": 10.0,      # Check every 10 seconds
        "auth_token": "Bearer YOUR_API_TOKEN_HERE"
    }
}
```

REAL-WORLD EXAMPLES:

Azure Sentinel:
```python
{
    "rest": {
        "api_url": "https://management.azure.com/subscriptions/{sub_id}/providers/Microsoft.OperationalInsights/workspaces/{workspace}/tables/SecurityEvent/query",
        "poll_interval": 30.0,
        "auth_token": "Bearer azure_token"
    }
}
```

Custom Enterprise API:
```python
{
    "rest": {
        "api_url": "https://api.internal.com/security/events",
        "poll_interval": 15.0,
        "auth_token": "Bearer eyJhbGciOiJIUzI1NiIs..."
    }
}
```

GET API TOKENS:
  Most platforms provide API tokens in:
  - Admin → API Management → Create Token
  - Settings → Security → API Keys
  - Profile → Integrations → New Integration

TROUBLESHOOTING:
  Error: "401 Unauthorized"
    → Token expired or invalid, regenerate in API settings
  
  Error: "Timeout"
    → Increase poll_interval, API is slow
  
  Error: "SSL: CERTIFICATE_VERIFY_FAILED"
    → Self-signed cert, add verify_certs = False

PERFORMANCE:
  - Typical throughput: 100-1,000 events/sec
  - Latency: depends on poll_interval
  - Good for moderate event volumes

================================================================================
6. WEBSOCKET CONNECTOR - Real-Time Streaming
================================================================================

WHAT IT DOES:
  Establishes WebSocket connection and receives events in real-time.
  Zero latency, immediate notifications when events occur.

REQUIREMENTS:
  ✓ WebSocket server/endpoint available
  ✓ WSS (secure) or WS (non-TLS) URL
  ✓ pip install websocket-client

CONFIGURATION TEMPLATE:
```python
{
    "websocket": {
        "url": "wss://events.soc.company.com:8443/stream",
        "max_retries": 5
    }
}
```

WITH AUTHENTICATION:
```python
{
    "websocket": {
        "url": "wss://api.siem.com/v1/events/stream",
        "auth_header": "Authorization: Bearer token_here",
        "max_retries": 10
    }
}
```

REAL-WORLD PLATFORMS:
  - Palo Alto Networks (AutoFocus API)
  - Rapid7 (InsightIDR WebSocket)
  - Custom Kafka WebSocket proxy
  - Alert management platforms

EXAMPLE USAGE:
```bash
export WEBSOCKET_URL=wss://alerts.company.local:8443/stream
python run_connector_advanced.py 4 websocket
```

TROUBLESHOOTING:
  Error: "Connection refused"
    → WebSocket server not running
  
  Error: "SSL: CERTIFICATE_VERIFY_FAILED"
    → Self-signed cert or cert mismatch
  
  Connection drops frequently?
    → Server force-closing idle connections, increase keep-alive

PERFORMANCE:
  - Latency: Real-time (<100ms)
  - Throughput: 1,000-10,000 events/sec
  - Best for: Critical alerts, live monitoring

================================================================================
7. WINDOWS EVENT LOG CONNECTOR - Native OS Events
================================================================================

WHAT IT DOES:
  Reads Windows Event Log directly from local or remote machine.
  Access to Security, System, Application, and custom event logs.

REQUIREMENTS:
  ✓ Windows operating system
  ✓ Admin privileges (for Security log access)
  ✓ pip install pywin32
  ✓ Run post-install: python -m pywin32_postinstall -install

CONFIGURATION TEMPLATE:
```python
{
    "windows_eventlog": {
        "log_name": "Security"      # or "System", "Application"
    }
}
```

COMMON LOG NAMES:
  "Security"              → Logon events, audit events
  "System"                → Driver loads, service events
  "Application"           → Application crashes, warnings
  "Microsoft-Windows-Sysmon/Operational"  → Sysmon data
  "ForwardedEvents"       → Events forwarded from other machines

REAL-WORLD EXAMPLE:
```bash
# Read all new Security Log events
python run_connector_advanced.py 4 windows_eventlog

# This will read events like:
# Event #1: HOST-WIN10 | T1078 | Account Logon (Security event 4624)
# Event #2: HOST-WIN10 | T1087 | User Enumeration (Security event 4720)
```

FOR REMOTE MACHINES:
```python
{
    "windows_eventlog": {
        "log_name": "Security",
        "computer": "\\\\HOSTNAME_OR_IP"
    }
}
```

TROUBLESHOOTING:
  Error: "(1314, 'OpenEventLogW', 'privilege not held')"
    → Run Python as Administrator or use different log
  
  No access to remote machines?
    → Check network access and credentials
  
  Sysmon events not showing?
    → Install Sysmon: https://docs.microsoft.com/sysinternals/downloads/sysmon

PERFORMANCE:
  - Latency: 1-2 seconds
  - Throughput: 100-1,000 events/sec
  - Good for: Single/few Windows machines

================================================================================

NOW CHOOSE YOUR SCENARIO AND DEPLOY!

Scenario 1: python run_connector_advanced.py 1  (Enterprise)
Scenario 2: python run_connector_advanced.py 2  (Cloud)
Scenario 3: python run_connector_advanced.py 3  (Hybrid)
Scenario 4: python run_connector_advanced.py 4  (Modern SOC)
Scenario 5: python run_connector_advanced.py 5  (Lightweight)

================================================================================
