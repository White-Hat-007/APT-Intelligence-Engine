#!/usr/bin/env python3
"""
Infrastructure Setup Orchestrator - Start all mock servers for testing
Manages: Mock REST API, WebSocket, Splunk, Kafka, Elasticsearch
"""

import subprocess
import time
import os
import sys
from threading import Thread, Event
import signal

# Cloud server processes
SERVERS = {
    'rest_api': {
        'script': 'mock_rest_api_server.py',
        'host': 'localhost',
        'port': 8443,
        'description': 'REST API Server (security events)',
        'process': None
    },
    'websocket': {
        'script': 'mock_websocket_server.py',
        'host': 'localhost',
        'port': 8443,
        'description': 'WebSocket Server (threat alerts)',
        'process': None
    },
    'splunk': {
        'script': 'mock_splunk_simulator.py',
        'host': 'localhost',
        'port': 8089,
        'description': 'Splunk Simulator (security events)',
        'process': None
    }
}

KAFKA_SETUP = """
# Kafka Setup (Optional - requires Docker)

1. Install Docker from: https://www.docker.com/products/docker-desktop

2. Start Kafka and Zookeeper:
   docker run -d --name zookeeper -p 2181:2181 \\
     -e ZOOKEEPER_CLIENT_PORT=2181 \\
     confluentinc/cp-zookeeper:latest
   
   docker run -d --name kafka -p 9092:9092 \\
     -e KAFKA_BROKER_ID=1 \\
     -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \\
     -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \\
     -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \\
     confluentinc/cp-kafka:latest

3. Create topic:
   docker exec kafka kaf-topics-shell --create --topic security-events \\
     --bootstrap-server localhost:9092 --partitions 1

4. Then set environment:
   $env:KAFKA_BROKERS='localhost:9092'
"""

ELASTICSEARCH_SETUP = """
# Elasticsearch Setup (Optional - requires Docker)

1. Install Docker from: https://www.docker.com/products/docker-desktop

2. Start Elasticsearch:
   docker run -d --name elasticsearch \\
     -e discovery.type=single-node \\
     -e xpack.security.enabled=false \\
     -p 9200:9200 \\
     docker.elastic.co/elasticsearch/elasticsearch:8.0.0

3. Verify it's running:
   curl http://localhost:9200

4. Then set environment:
   $env:ELASTIC_HOSTS='localhost:9200'
"""

def print_banner():
    """Print setup banner"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  APT THREAT INTELLIGENCE ENGINE - INFRASTRUCTURE SETUP             ║
║                                                                    ║
║  Starting Mock Infrastructure for All 7 Connectors                ║
╚════════════════════════════════════════════════════════════════════╝
    """)

def print_status():
    """Print current infrastructure status"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  INFRASTRUCTURE STATUS                                             ║
╚════════════════════════════════════════════════════════════════════╝

RUNNING MOCK SERVERS (No Installation Needed):
  ✓ REST API Server      → http://localhost:8443/v1/events
  ✓ WebSocket Server     → wss://localhost:8443/stream
  ✓ Splunk Simulator     → localhost:8089

ALREADY AVAILABLE:
  ✓ Syslog Listener      → localhost:514 (built-in)
  ✓ Windows Event Log    → Built-in Windows events

OPTIONAL (Requires Docker):
  ○ Kafka                → localhost:9092 (see below for setup)
  ○ Elasticsearch        → localhost:9200 (see below for setup)

    """)

def start_server(server_name, script_path):
    """Start a single mock server"""
    server_info = SERVERS[server_name]
    try:
        print(f"\n[startup] Starting {server_info['description']}...")
        
        # Start Python script in a new process
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=os.getcwd()
        )
        
        SERVERS[server_name]['process'] = process
        
        # Print output in background
        def print_output():
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
        
        output_thread = Thread(target=print_output, daemon=True)
        output_thread.start()
        
        time.sleep(1)  # Give server time to start
        print(f"[startup] ✓ {server_name} started on {server_info['host']}:{server_info['port']}")
        
    except Exception as e:
        print(f"[startup] ✗ Failed to start {server_name}: {e}")

def start_all_servers():
    """Start all mock servers"""
    print_banner()
    print("[startup] Starting mock infrastructure...\n")
    
    for server_name, info in SERVERS.items():
        script = info['script']
        start_server(server_name, script)
    
    print_status()

def print_deployment_guide():
    """Print guide for deploying connectors"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  DEPLOYMENT GUIDE                                                  ║
╚════════════════════════════════════════════════════════════════════╝

NOW RUNNING WITH MOCK INFRASTRUCTURE:

1. In a NEW TERMINAL, set environment variables:

   PowerShell:
   $env:SPLUNK_HOST='localhost:8089'
   $env:SPLUNK_USER='admin'
   $env:SPLUNK_PASSWORD='admin'
   $env:REST_API_URL='http://localhost:8443/v1/events'
   $env:WEBSOCKET_URL='wss://localhost:8443/stream'
   $env:KAFKA_BROKERS='localhost:9092'
   $env:ELASTIC_HOSTS='localhost:9200'

2. Deploy all 7 connectors:

   python run_connector_advanced.py 4

3. In ANOTHER terminal, send test events:

   python send_syslog.py localhost 514 5

4. Watch events flow through the system:
   - REST API events        ← Mock server
   - WebSocket alerts       ← Mock server
   - Splunk queries         ← Mock simulator
   - Syslog events          ← Your test sender
   - Windows Event Log      ← Local Windows events

═══════════════════════════════════════════════════════════════════════

OPTIONAL: Add Real Kafka/Elasticsearch (requires Docker):
""" + KAFKA_SETUP + ELASTICSEARCH_SETUP + """

═══════════════════════════════════════════════════════════════════════

4. CONNECTORS STATUS AFTER DEPLOYMENT:

   ✓ REST API             - Polling http://localhost:8443/v1/events
   ✓ WebSocket            - Streaming wss://localhost:8443/stream
   ✓ Splunk               - Connected to localhost:8089
   ✓ Syslog               - Listening on localhost:514
   ✓ Windows Event Log    - Reading local Security log (if admin)
   ○ Kafka                - Waiting for broker (optional)
   ○ Elasticsearch        - Waiting for cluster (optional)

═══════════════════════════════════════════════════════════════════════
    """)

def cleanup(signum=None, frame=None):
    """Cleanup and shutdown all servers"""
    print("\n[shutdown] Cleaning up mock infrastructure...")
    for server_name, info in SERVERS.items():
        if info['process']:
            try:
                info['process'].terminate()
                info['process'].wait(timeout=2)
                print(f"[shutdown] ✓ Stopped {server_name}")
            except:
                info['process'].kill()
                print(f"[shutdown] ✓ Killed {server_name}")
    
    print("[shutdown] Infrastructure shutdown complete")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    start_all_servers()
    print_deployment_guide()
    
    print("\n[info] Infrastructure running. Press Ctrl+C to stop all servers.")
    
    try:
        # Keep running until user exits
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()
