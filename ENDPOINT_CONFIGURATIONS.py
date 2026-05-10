#!/usr/bin/env python3
"""
REAL ENDPOINT CONFIGURATIONS
For each connector type with realistic examples from real deployments
"""

# ============================================================================
# SCENARIO 1: ENTERPRISE SPLUNK + SYSLOG SETUP (Most Common)
# ============================================================================

SCENARIO_1_SPLUNK = {
    "splunk": {
        "host": "splunk.mycompany.local:8089",
        "username": "apt_detector",
        "password": "Y0urSecurePassword123!",  # Use environment variable in production!
        "search_query": """
            (sourcetype=sysmon OR sourcetype=windows_security OR 
             sourcetype=linux_audit) 
            (EventCode=1 OR EventCode=3 OR EventCode=5 OR EventCode=11 OR
             EventCode=21 OR EventCode=23)
            earliest=-10m latest=now
        """
    },
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    }
}

# ============================================================================
# SCENARIO 2: CLOUD-NATIVE KAFKA + ELASTICSEARCH
# ============================================================================

SCENARIO_2_CLOUD_NATIVE = {
    "kafka": {
        "bootstrap_servers": [
            "kafka-broker1.cloud.local:9092",
            "kafka-broker2.cloud.local:9092",
            "kafka-broker3.cloud.local:9092"
        ],
        "topic": "security.events.raw",
        "group_id": "apt_threat_intelligence",
        "auto_offset_reset": "latest"
    },
    "elastic": {
        "hosts": [
            "elasticsearch1.cloud.local:9200",
            "elasticsearch2.cloud.local:9200"
        ],
        "index_pattern": "logs-sysmon-*,logs-osquery-*,logs-auditd-*",
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
                                "network",
                                "authentication"
                            ]
                        }
                    }
                ]
            }
        }
    }
}

# ============================================================================
# SCENARIO 3: HYBRID SETUP (Splunk + Kafka + REST API)
# ============================================================================

SCENARIO_3_HYBRID = {
    "splunk": {
        "host": "splunk.internal.local:8089",
        "username": "admin",
        "password": "SecurePassword123",
        "search_query": "sourcetype=sysmon index=main earliest=-30m latest=now"
    },
    "kafka": {
        "bootstrap_servers": ["kafka.internal.local:9092"],
        "topic": "security.alerts"
    },
    "rest": {
        "api_url": "https://api.yoursiem.com/api/v2/events",
        "poll_interval": 10.0,
        "auth_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}

# ============================================================================
# SCENARIO 4: MODERN SOC (Everything + WebSocket)
# ============================================================================

SCENARIO_4_MODERN_SOC = {
    "splunk": {
        "host": "splunk-master.soc.local:8089",
        "username": "threat_intel",
        "password": "ComplexPassword123!@#",
        "search_query": """
            (sourcetype=sysmon OR sourcetype=windows_security OR 
             sourcetype=zeek OR sourcetype=suricata)
            (EventCode=1 OR EventCode=3 OR EventCode=5 OR EventCode=11 OR
             protocol=tcp OR protocol=udp)
            earliest=-15m latest=now
        """
    },
    "kafka": {
        "bootstrap_servers": [
            "kafka1.soc.local:9092",
            "kafka2.soc.local:9092",
            "kafka3.soc.local:9092"
        ],
        "topic": "soc.security.raw"
    },
    "elastic": {
        "hosts": [
            "es1.soc.local:9200",
            "es2.soc.local:9200",
            "es3.soc.local:9200"
        ],
        "index_pattern": "logs-*"
    },
    "websocket": {
        "url": "wss://alerts.soc.local:8443/stream",
        "max_retries": 10
    },
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "tcp"
    }
}

# ============================================================================
# SCENARIO 5: MINIMAL SETUP (Syslog Only - No Dependencies!)
# ============================================================================

SCENARIO_5_LIGHTWEIGHT = {
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    }
}

# ============================================================================
# REAL-WORLD EXAMPLES FROM ACTUAL DEPLOYMENTS
# ============================================================================

# Example 1: Fortune 500 Enterprise
FORTUNE_500_ENTERPRISE = {
    "splunk": {
        "host": "splunk-indexer-01.corp.internal:8089",
        "username": "splunk_api_user",
        "password": "$(echo $SPLUNK_PASSWORD)",  # Load from env
        "search_query": """
            index=windows_security OR index=sysmon OR index=linux_audit
            (EventCode=4688 OR EventCode=4689 OR EventCode=5156 OR 
             process_name=powershell.exe)
            earliest=-5m latest=now
        """
    },
    "syslog": {
        "host": "syslog-aggregator.corp.internal",
        "port": 514,
        "protocol": "tcp"
    }
}

# Example 2: AWS/Cloud Environment
AWS_ENVIRONMENT = {
    "kafka": {
        "bootstrap_servers": [
            "kafka-broker-1.ec2.amazonaws.com:9092",
            "kafka-broker-2.ec2.amazonaws.com:9092"
        ],
        "topic": "cloudtril-events"
    },
    "elastic": {
        "hosts": ["opensearch-domain.us-east-1.es.amazonaws.com:443"],
        "index_pattern": "cwl-*"
    }
}

# Example 3: Managed Security Service Provider (MSSP)
MSSP_PROVIDER = {
    "rest": {
        "api_url": "https://api.mssp.provider/v1/customer/{customer_id}/events",
        "poll_interval": 5.0,
        "auth_token": "Bearer LONG_OAUTH_TOKEN_HERE"
    },
    "websocket": {
        "url": "wss://stream.mssp.provider/v1/events",
        "max_retries": 5
    }
}

# ============================================================================
# CONFIGURATION TEMPLATE (Copy and Modify)
# ============================================================================

TEMPLATE_MINIMAL = {
    "syslog": {
        "host": "YOUR_SYSLOG_SERVER_IP",
        "port": 514,
        "protocol": "udp"  # or "tcp"
    }
}

TEMPLATE_FULL = {
    "kafka": {
        "bootstrap_servers": [
            "YOUR_KAFKA_BROKER_1:9092",
            "YOUR_KAFKA_BROKER_2:9092"
        ],
        "topic": "YOUR_TOPIC_NAME",
        "group_id": "apt_detector"
    },
    "splunk": {
        "host": "YOUR_SPLUNK_HOST:8089",
        "username": "YOUR_USERNAME",
        "password": "YOUR_PASSWORD",
        "search_query": "YOUR_SEARCH_QUERY"
    },
    "elastic": {
        "hosts": [
            "YOUR_ELASTICSEARCH_HOST:9200"
        ],
        "index_pattern": "YOUR_INDEX_PATTERN",
        "query": {
            "match_all": {}
        }
    },
    "websocket": {
        "url": "wss://YOUR_WEBSOCKET_URL",
        "max_retries": 3
    },
    "rest": {
        "api_url": "https://YOUR_API_ENDPOINT",
        "poll_interval": 10.0,
        "auth_token": "Bearer YOUR_TOKEN"
    },
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    },
    "windows_eventlog": {
        "log_name": "Security"
    }
}

# ============================================================================
# HOW TO USE THESE CONFIGURATIONS
# ============================================================================

"""
Step 1: Choose Your Scenario
    - SCENARIO_1_SPLUNK: Traditional enterprise
    - SCENARIO_2_CLOUD_NATIVE: Kubernetes/Cloud
    - SCENARIO_3_HYBRID: Mixed environment
    - SCENARIO_4_MODERN_SOC: Full-featured SOC
    - SCENARIO_5_LIGHTWEIGHT: Minimal dependencies

Step 2: Copy to run_connector.py
    Replace CONNECTOR_CONFIGS in run_connector.py with your scenario

Step 3: Customize Values
    Replace placeholder values with your actual infrastructure:
    - Hostnames/IPs
    - Ports
    - Credentials
    - Topic/Index names
    - Search queries

Step 4: Secure Your Credentials
    NEVER hardcode passwords!
    Use environment variables instead:
    
    import os
    password = os.getenv('SPLUNK_PASSWORD')  # Read from environment
    
Step 5: Run!
    python run_connector.py all

Example:
    export SPLUNK_PASSWORD=your_secure_password
    export KAFKA_BROKERS=kafka1.local:9092,kafka2.local:9092
    python run_connector.py all
"""

# ============================================================================
# COMMON ISSUES & FIXES
# ============================================================================

TROUBLESHOOTING = """
Issue: "NoBrokersAvailable"
Fix: Check Kafka brokers are running and reachable
     Test: telnet kafka.local 9092

Issue: "Connection refused"
Fix: Verify endpoint is correct and service is running
     Test: curl https://your-endpoint:port

Issue: "Authentication failed"
Fix: Check username/password and permissions
     For Splunk: Verify user has 'search' capability
     For ES: Verify user has 'read' permission on index

Issue: "Timeout"
Fix: Increase poll_interval for slow networks
     Check network connectivity to endpoint

Issue: "ImportError" on Kafka, Splunk, etc.
Fix: Install missing package:
     pip install kafka-python splunk-sdk elasticsearch websocket-client pywin32
"""

if __name__ == "__main__":
    print("=" * 70)
    print("REAL ENDPOINT CONFIGURATION REFERENCE")
    print("=" * 70)
    print("\nAvailable scenarios:")
    print("1. SCENARIO_1_SPLUNK - Traditional enterprise (Splunk + Syslog)")
    print("2. SCENARIO_2_CLOUD_NATIVE - Cloud environment (Kafka + Elasticsearch)")
    print("3. SCENARIO_3_HYBRID - Mixed setup (Splunk + Kafka + REST)")
    print("4. SCENARIO_4_MODERN_SOC - Full-featured SOC (all connectors)")
    print("5. SCENARIO_5_LIGHTWEIGHT - Minimal setup (Syslog only)")
    print("\nReal-world examples:")
    print("- FORTUNE_500_ENTERPRISE")
    print("- AWS_ENVIRONMENT")
    print("- MSSP_PROVIDER")
    print("\nSee the code above for configuration details!")
    print("=" * 70)
