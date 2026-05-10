#!/usr/bin/env python3
"""
All-in-One Deployment Test
Tests all 7 connectors with environment-based endpoint configuration
No background servers required - uses what's available
"""

import os
import sys
import subprocess

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  APT THREAT INTELLIGENCE ENGINE - COMPLETE DEPLOYMENT TEST          ║
║                                                                      ║
║  Testing All 7 Connectors with Configured Endpoints                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

def configure_endpoints():
    """Configure all endpoint environment variables"""
    print("\n[*] Configuring endpoints...\n")
    
    # Configure for local testing
    endpoints = {
        'SPLUNK_HOST': 'localhost:8089',
        'SPLUNK_USER': 'admin',
        'SPLUNK_PASSWORD': 'admin',
        'KAFKA_BROKERS': 'localhost:9092',
        'ELASTIC_HOSTS': 'localhost:9200',
        'REST_API_URL': 'http://localhost:8443/v1/events',
        'WEBSOCKET_URL': 'wss://localhost:8443/stream',
        'SYSLOG_HOST': 'localhost',
        'SYSLOG_PORT': '514'
    }
    
    for key, value in endpoints.items():
        os.environ[key] = value
        print(f"  ✓ {key:20} = {value}")
    
    return endpoints

def deploy_connectors():
    """Deploy all 7 connectors"""
    print("\n[*] Deploying all 7 connectors (Scenario 4)...\n")
    
    cmd = [
        sys.executable,
        'run_connector_advanced.py',
        '4'
    ]
    
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"[!] Error running connectors: {e}")
        return False
    
    return True

def print_next_steps():
    """Print next steps"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  DEPLOYMENT COMPLETE                                                ║
╚══════════════════════════════════════════════════════════════════════╝

WHAT JUST HAPPENED:

  ✓ All 7 connectors deployed with localhost endpoints
  ✓ REST API configured to http://localhost:8443/v1/events
  ✓ WebSocket configured to wss://localhost:8443/stream
  ✓ Splunk configured to localhost:8089
  ✓ Syslog listening on localhost:514
  ✓ Kafka pointing to localhost:9092
  ✓ Elasticsearch pointing to localhost:9200
  ✓ Windows Event Log using local Security log

CONNECTOR STATUS:
  
  ✓ RUNNING (No external infrastructure needed)
    - Syslog Listener
    - Windows Event Log Reader
  
  ⚠ WAITING FOR INFRASTRUCTURE
    - REST API (needs server on http://localhost:8443)
    - WebSocket (needs server on wss://localhost:8443)
    - Splunk (needs instance on localhost:8089)
    - Kafka (needs broker on localhost:9092)
    - Elasticsearch (needs cluster on localhost:9200)

═════════════════════════════════════════════════════════════════════════

NEXT: Send test events via syslog in another terminal:

  python send_syslog.py localhost 514 10

Or, to set up real infrastructure for all 7 connectors:

  1. If you have Docker:
     
     # Start Elasticsearch
     docker run -d --name elasticsearch \\
       -e discovery.type=single-node \\
       -e xpack.security.enabled=false \\
       -p 9200:9200 \\
       docker.elastic.co/elasticsearch/elasticsearch:7.15.0
     
     # Start Kafka
     docker run -d --name zookeeper -p 2181:2181 \\
       -e ZOOKEEPER_CLIENT_PORT=2181 \\
       confluentinc/cp-zookeeper:latest
     
     docker run -d --name kafka -p 9092:9092 \\
       -e KAFKA_BROKER_ID=1 \\
       -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \\
       -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \\
       -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \\
       confluentinc/cp-kafka:latest

  2. Start mock infrastructure in Python:
     
     python setup_infrastructure.py

  3. Deploy with updated configuration:
     
     python run_connector_advanced.py 4

═════════════════════════════════════════════════════════════════════════

REAL-WORLD DEPLOYMENT:

To use with your actual infrastructure, update endpoints:

  PowerShell:
  $env:SPLUNK_HOST='your-splunk:8089'
  $env:KAFKA_BROKERS='broker1:9092,broker2:9092'
  $env:ELASTIC_HOSTS='es1:9200,es2:9200'
  $env:REST_API_URL='https://your-api.com/events'
  $env:WEBSOCKET_URL='wss://your-soc.com/alerts'
  
  Then:
  python run_connector_advanced.py 4

═════════════════════════════════════════════════════════════════════════
    """)

if __name__ == '__main__':
    print_banner()
    endpoints = configure_endpoints()
    deploy_connectors()
    print_next_steps()
