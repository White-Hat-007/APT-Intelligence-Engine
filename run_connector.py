#!/usr/bin/env python3
"""
Simple Multi-Connector Runner
Run any of the 7 connectors directly without editing files
Supports custom endpoints via environment variables or config files
"""

import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion.connectors import get_connector

# ============================================================================
# REALISTIC ENDPOINT CONFIGURATIONS
# ============================================================================
# These are example configurations for real-world deployments
# Replace with your actual infrastructure details
# 
# SECURITY NOTE: Never hardcode passwords! Use environment variables:
#   password = os.getenv('SPLUNK_PASSWORD')
# ============================================================================

# SCENARIO 1: Enterprise Splunk + Syslog (Most Common)
SCENARIO_ENTERPRISE = {
    "splunk": {
        "host": os.getenv('SPLUNK_HOST', "splunk.mycompany.local:8089"),
        "username": os.getenv('SPLUNK_USER', "apt_detector"),
        "password": os.getenv('SPLUNK_PASSWORD', "changeme"),
        "search_query": """
            (sourcetype=sysmon OR sourcetype=windows_security) 
            (EventCode=1 OR EventCode=3 OR EventCode=5)
            earliest=-10m latest=now
        """
    },
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    }
}

# SCENARIO 2: Cloud-Native (Kafka + Elasticsearch)
SCENARIO_CLOUD = {
    "kafka": {
        "bootstrap_servers": os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
        "topic": os.getenv('KAFKA_TOPIC', "security.events.raw"),
        "group_id": "apt_threat_intelligence"
    },
    "elastic": {
        "hosts": os.getenv('ELASTIC_HOSTS', 'localhost:9200').split(','),
        "index_pattern": "logs-sysmon-*",
        "query": {"match_all": {}}
    }
}

# SCENARIO 3: Modern SOC (Everything)
SCENARIO_SOC = {
    "splunk": {
        "host": os.getenv('SPLUNK_HOST', "splunk.local:8089"),
        "username": os.getenv('SPLUNK_USER', "admin"),
        "password": os.getenv('SPLUNK_PASSWORD', "password"),
        "search_query": "sourcetype=sysmon earliest=-15m latest=now"
    },
    "kafka": {
        "bootstrap_servers": os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
        "topic": "security.events"
    },
    "elastic": {
        "hosts": os.getenv('ELASTIC_HOSTS', 'localhost:9200').split(','),
        "index_pattern": "logs-*"
    },
    "websocket": {
        "url": os.getenv('WEBSOCKET_URL', "wss://localhost:8443/stream"),
        "max_retries": 3
    },
    "rest": {
        "api_url": os.getenv('REST_API_URL', "https://api.local/events"),
        "poll_interval": 10.0,
        "auth_token": os.getenv('REST_TOKEN', "Bearer token_here")
    },
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    }
}

# DEFAULT: Lightweight setup (Syslog only - no dependencies needed)
SCENARIO_LIGHTWEIGHT = {
    "syslog": {
        "host": "0.0.0.0",
        "port": 514,
        "protocol": "udp"
    }
}

def show_menu():
    """Display connector selection menu"""
    print("\n" + "="*70)
    print("  APT THREAT INTELLIGENCE ENGINE")
    print("  SINGLE CONNECTOR RUNNER")
    print("="*70)
    print("\nAvailable Connectors:\n")
    
    connectors = list(CONNECTOR_CONFIGS.keys())
    for i, connector in enumerate(connectors, 1):
        config = CONNECTOR_CONFIGS[connector]
        print(f"  {i}) {connector}")
        for key, val in config.items():
            if key not in ['password']:  # Hide sensitive data
                print(f"       - {key}: {val}")
    
    print(f"\n  {len(connectors)+1}) Run ALL connectors in parallel")
    print(f"  {len(connectors)+2}) Exit")
    print("\n" + "="*70)
    print("Enter your choice: ", end="")
    
    try:
        choice = int(input().strip())
        return choice
    except ValueError:
        return -1

def run_single_connector(connector_name):
    """Run a single connector"""
    print(f"\n[*] Initializing {connector_name}...")
    print(f"[*] Configuration: {CONNECTOR_CONFIGS[connector_name]}")
    print("[*] Attempting connection...")
    
    try:
        event_stream = get_connector(connector_name, **CONNECTOR_CONFIGS[connector_name])
        print(f"[+] {connector_name} connected! Processing events...")
        print("[*] (Press Ctrl+C to stop)\n")
        
        event_count = 0
        for event in event_stream:
            event_count += 1
            host = event.get("host", "unknown")
            timestamp = event.get("timestamp", "N/A")
            technique = event.get("technique_id", "N/A")
            
            if event_count % 5 == 1:  # Show every 5th event
                print(f"[{connector_name:15}] Event #{event_count}: {host:20} | {technique:10} | {timestamp}")
            
            if event_count >= 10:  # Demo: stop after 10 events
                print(f"\n[*] Demo: Processed {event_count} events. Stopping...")
                break
    
    except KeyboardInterrupt:
        print(f"\n\n[*] {connector_name} stopped by user")
    except Exception as e:
        print(f"\n[-] Error with {connector_name}: {type(e).__name__}: {e}")
        print(f"[*] Make sure the {connector_name} endpoint is reachable and credentials are correct")

def run_all_connectors():
    """Run all 7 connectors in parallel threads"""
    import threading
    from collections import defaultdict
    
    class ConnectorThread(threading.Thread):
        def __init__(self, connector_name):
            super().__init__(daemon=True, name=f"connector-{connector_name}")
            self.connector_name = connector_name
            self.event_count = 0
            self.errors = 0
        
        def run(self):
            try:
                print(f"[+] {self.connector_name}: Initializing...")
                event_stream = get_connector(
                    self.connector_name, 
                    **CONNECTOR_CONFIGS[self.connector_name]
                )
                
                for event in event_stream:
                    self.event_count += 1
                    if self.event_count % 10 == 1:
                        host = event.get("host", "?")
                        print(f"[{self.connector_name:15}] Event #{self.event_count}: {host}")
                    
                    if self.event_count >= 50:  # Demo limit
                        break
            
            except Exception as e:
                self.errors += 1
                print(f"[{self.connector_name:15}] Error: {type(e).__name__}")
    
    print("\n[*] Starting all 7 connectors in parallel threads...")
    print("[*] Each will attempt to connect and process events")
    print("[*] (Press Ctrl+C to stop all)\n")
    
    threads = []
    for connector_name in CONNECTOR_CONFIGS.keys():
        thread = ConnectorThread(connector_name)
        thread.start()
        threads.append(thread)
    
    try:
        # Wait for all threads with a timeout
        import time
        timeout = 30
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            active = sum(1 for t in threads if t.is_alive())
            if active == 0:
                break
            time.sleep(0.5)
        
        # Print summary
        print("\n" + "="*70)
        print("FINAL REPORT")
        print("="*70)
        for thread in threads:
            status = "Running" if thread.is_alive() else "Completed"
            print(f"{thread.connector_name:15} | Events: {thread.event_count:5} | Errors: {thread.errors:3} | {status}")
        print("="*70 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n[*] Stopping all connectors...")
        for thread in threads:
            if thread.is_alive():
                print(f"    Waiting for {thread.connector_name}...")
        
        # Brief timeout
        import time
        for thread in threads:
            thread.join(timeout=2)
        
        print("[*] All connectors stopped\n")

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Command line mode
        connector = sys.argv[1].lower()
        if connector == "all":
            run_all_connectors()
        elif connector in CONNECTOR_CONFIGS:
            run_single_connector(connector)
        else:
            print(f"Unknown connector: {connector}")
            print(f"Available: {', '.join(CONNECTOR_CONFIGS.keys())}, all")
        return
    
    # Interactive mode
    while True:
        choice = show_menu()
        connectors = list(CONNECTOR_CONFIGS.keys())
        
        if choice == len(connectors) + 1:
            run_all_connectors()
        elif choice == len(connectors) + 2:
            print("\n[*] Exiting...\n")
            break
        elif 1 <= choice <= len(connectors):
            connector_name = connectors[choice - 1]
            run_single_connector(connector_name)
        else:
            print("\n[-] Invalid choice. Try again.")

if __name__ == "__main__":
    main()
