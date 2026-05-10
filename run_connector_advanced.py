#!/usr/bin/env python3
"""
ADVANCED CONNECTOR RUNNER WITH SCENARIO SUPPORT
Runs connectors with realistic endpoint configurations
Supports multiple infrastructure scenarios with environment variable overrides
"""

import sys
import os
import json
import threading
from collections import defaultdict
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ingestion.connectors import get_connector

# ============================================================================
# REALISTIC ENDPOINT CONFIGURATIONS FOR DIFFERENT SCENARIOS
# ============================================================================

# SCENARIO 1: Enterprise Splunk + Syslog (Most Common)
SCENARIO_ENTERPRISE = {
    "name": "Enterprise Splunk + Syslog",
    "description": "Traditional SOC with Splunk SIEM and Syslog aggregation",
    "connectors": {
        "splunk": {
            "host": os.getenv('SPLUNK_HOST', "splunk.mycompany.local:8089"),
            "username": os.getenv('SPLUNK_USER', "apt_detector"),
            "password": os.getenv('SPLUNK_PASSWORD', "Y0urSecurePassword123!"),
            "search_query": "(sourcetype=sysmon OR sourcetype=windows_security) (EventCode=1 OR EventCode=3 OR EventCode=5 OR EventCode=11) earliest=-10m latest=now"
        },
        "syslog": {
            "host": "0.0.0.0",
            "port": int(os.getenv('SYSLOG_PORT', '514')),
            "protocol": os.getenv('SYSLOG_PROTOCOL', 'udp')
        }
    }
}

# SCENARIO 2: Cloud-Native (Kafka + Elasticsearch)
SCENARIO_CLOUD = {
    "name": "Cloud-Native (Kafka + Elasticsearch)",
    "description": "Modern cloud architecture with Kafka streaming and ELK Stack",
    "connectors": {
        "kafka": {
            "bootstrap_servers": os.getenv('KAFKA_BROKERS', 'kafka.cloud.local:9092').split(','),
            "topic": os.getenv('KAFKA_TOPIC', "security.events.raw"),
            "group_id": "apt_threat_intelligence"
        },
        "elastic": {
            "hosts": os.getenv('ELASTIC_HOSTS', 'elasticsearch.cloud.local:9200').split(','),
            "index_pattern": "logs-sysmon-*,logs-osquery-*",
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": "now-1h"}}}
                    ]
                }
            }
        }
    }
}

# SCENARIO 3: Hybrid (Everything)
SCENARIO_HYBRID = {
    "name": "Hybrid Setup (Splunk + Kafka + REST)",
    "description": "Mixed environment combining multiple data sources",
    "connectors": {
        "splunk": {
            "host": os.getenv('SPLUNK_HOST', "splunk.internal.local:8089"),
            "username": os.getenv('SPLUNK_USER', "admin"),
            "password": os.getenv('SPLUNK_PASSWORD', "password"),
            "search_query": "sourcetype=sysmon earliest=-30m latest=now"
        },
        "kafka": {
            "bootstrap_servers": os.getenv('KAFKA_BROKERS', 'kafka.internal.local:9092').split(','),
            "topic": os.getenv('KAFKA_TOPIC', "security.alerts")
        },
        "rest": {
            "api_url": os.getenv('REST_API_URL', "https://api.yoursiem.com/api/v2/events"),
            "poll_interval": 10.0,
            "auth_token": os.getenv('REST_TOKEN', "Bearer YOUR_API_TOKEN")
        }
    }
}

# SCENARIO 4: Modern SOC (All 7 Connectors)
SCENARIO_SOC = {
    "name": "Modern SOC (All Connectors)",
    "description": "Full-featured SOC with all 7 data sources",
    "connectors": {
        "splunk": {
            "host": os.getenv('SPLUNK_HOST', "splunk-master.soc.local:8089"),
            "username": os.getenv('SPLUNK_USER', "threat_intel"),
            "password": os.getenv('SPLUNK_PASSWORD', "ComplexPassword123!"),
            "search_query": "(sourcetype=sysmon OR sourcetype=zeek) (EventCode=1 OR EventCode=3) earliest=-15m"
        },
        "kafka": {
            "bootstrap_servers": os.getenv('KAFKA_BROKERS', 'kafka1.soc.local:9092,kafka2.soc.local:9092').split(','),
            "topic": os.getenv('KAFKA_TOPIC', "soc.security.raw")
        },
        "elastic": {
            "hosts": os.getenv('ELASTIC_HOSTS', 'es1.soc.local:9200').split(','),
            "index_pattern": "logs-*"
        },
        "websocket": {
            "url": os.getenv('WEBSOCKET_URL', "wss://alerts.soc.local:8443/stream"),
            "max_retries": 10
        },
        "rest": {
            "api_url": os.getenv('REST_API_URL', "https://api.soc.local/v1/events"),
            "poll_interval": 10.0,
            "auth_token": os.getenv('REST_TOKEN', "Bearer soc_api_token")
        },
        "syslog": {
            "host": "0.0.0.0",
            "port": 514,
            "protocol": "tcp"
        },
        "windows_eventlog": {
            "log_name": "Security"
        }
    }
}

# SCENARIO 5: Lightweight (Syslog Only - No Dependencies)
SCENARIO_LIGHTWEIGHT = {
    "name": "Lightweight (Syslog Only)",
    "description": "Minimal setup using only stdlib (no external dependencies needed)",
    "connectors": {
        "syslog": {
            "host": "0.0.0.0",
            "port": 514,
            "protocol": "udp"
        }
    }
}

# Map all scenarios
ALL_SCENARIOS = {
    "1": SCENARIO_ENTERPRISE,
    "2": SCENARIO_CLOUD,
    "3": SCENARIO_HYBRID,
    "4": SCENARIO_SOC,
    "5": SCENARIO_LIGHTWEIGHT
}

def show_scenario_menu():
    """Display scenario selection menu"""
    print("\n" + "="*80)
    print("  APT THREAT INTELLIGENCE ENGINE - ADVANCED CONNECTOR RUNNER")
    print("="*80)
    print("\nStep 1: SELECT YOUR INFRASTRUCTURE SCENARIO\n")
    
    for key, scenario in ALL_SCENARIOS.items():
        print(f"  {key}) {scenario['name']}")
        print(f"     {scenario['description']}")
        print()
    
    print("  6) Configure Custom Scenario")
    print("  7) Exit\n")
    
    print("="*80)
    print("Enter scenario (1-7): ", end="")
    
    return input().strip() or "1"

def show_connector_menu(scenario):
    """Display connector selection menu for a scenario"""
    print("\n" + "="*80)
    print(f"  SCENARIO: {scenario['name']}")
    print("="*80)
    print("\nStep 2: SELECT CONNECTORS TO RUN\n")
    
    connectors = list(scenario['connectors'].keys())
    
    for i, conn in enumerate(connectors, 1):
        config = scenario['connectors'][conn]
        host_info = config.get('host', config.get('hosts', config.get('url', 'N/A')))
        print(f"  {i}) {conn:18} - {str(host_info)[:40]}")
    
    print(f"  {len(connectors)+1}) ALL connectors")
    print(f"  {len(connectors)+2}) Back to scenarios\n")
    
    print("="*80)
    print("Enter choice (comma-separated for multiple): ", end="")
    
    choice = input().strip() or str(len(connectors)+1)
    
    if choice == str(len(connectors)+2):
        return None, None
    elif choice == str(len(connectors)+1):
        return scenario['connectors'], "all"
    else:
        try:
            indices = [int(x.strip())-1 for x in choice.split(",")]
            selected = {
                connectors[i]: scenario['connectors'][connectors[i]]
                for i in indices if 0 <= i < len(connectors)
            }
            return selected, "custom"
        except:
            print("\n[-] Invalid selection")
            return None, None

def run_connector(connector_name, config, max_events=50):
    """Run a single connector"""
    try:
        print(f"\n[{connector_name}] Initializing...")
        print(f"[{connector_name}] Config: {config}")
        
        event_stream = get_connector(connector_name, **config)
        print(f"[{connector_name}] Connected! Processing events...")
        
        event_count = 0
        for event in event_stream:
            event_count += 1
            
            host = event.get("host", "unknown")
            timestamp = event.get("timestamp", "N/A")
            technique = event.get("technique_id", "N/A")
            
            if event_count % 5 == 1:
                print(f"[{connector_name:15}] Event #{event_count}: {host:20} | {technique:10} | {timestamp}")
            
            if event_count >= max_events:
                print(f"[{connector_name}] Demo limit ({max_events} events) reached")
                break
    
    except KeyboardInterrupt:
        print(f"\n[{connector_name}] Stopped by user")
    except Exception as e:
        print(f"[{connector_name}] Error: {type(e).__name__}: {str(e)[:100]}")

def run_all_connectors_parallel(connectors_config):
    """Run all connectors in parallel threads"""
    
    class ConnectorThread(threading.Thread):
        def __init__(self, connector_name, config):
            super().__init__(daemon=True, name=f"conn-{connector_name}")
            self.connector_name = connector_name
            self.config = config
            self.event_count = 0
            self.errors = 0
        
        def run(self):
            try:
                print(f"[{self.connector_name}] Starting...")
                event_stream = get_connector(self.connector_name, **self.config)
                
                for event in event_stream:
                    self.event_count += 1
                    if self.event_count % 10 == 1:
                        host = event.get("host", "?")
                        print(f"[{self.connector_name:15}] Event #{self.event_count}: {host}")
                    
                    if self.event_count >= 50:  # Demo limit
                        break
            
            except Exception as e:
                self.errors += 1
                print(f"[{self.connector_name}] Error: {type(e).__name__}")
    
    print("\n" + "="*80)
    print("RUNNING ALL SELECTED CONNECTORS IN PARALLEL")
    print("="*80)
    print("\n[*] Starting connectors...")
    print("[*] (Press Ctrl+C to stop all)\n")
    
    threads = []
    for connector_name, config in connectors_config.items():
        print(f"[+] Launching {connector_name}...")
        thread = ConnectorThread(connector_name, config)
        thread.start()
        threads.append(thread)
    
    try:
        # Wait for threads with timeout
        import time
        timeout = 40
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            active = sum(1 for t in threads if t.is_alive())
            if active == 0:
                break
            time.sleep(0.5)
        
        # Print summary
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        print(f"{'Connector':<18} | {'Events':<8} | {'Errors':<6} | {'Status':<12}")
        print("-"*80)
        
        for thread in threads:
            status = "Running" if thread.is_alive() else "Completed"
            print(f"{thread.connector_name:<18} | {thread.event_count:<8} | {thread.errors:<6} | {status:<12}")
        
        print("="*80 + "\n")
    
    except KeyboardInterrupt:
        print("\n\n[*] Stopping all connectors...")
        for thread in threads:
            thread.join(timeout=2)
        print("[*] All connectors stopped\n")

def main():
    """Main entry point"""
    # Command-line mode
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            print("\nAvailable Scenarios:")
            for key, scenario in ALL_SCENARIOS.items():
                print(f"  {key}) {scenario['name']}")
            print("\nUsage: python run_connector_advanced.py [scenario] [connector]")
            print("Example: python run_connector_advanced.py 1 splunk kafka")
            return
        
        scenario_key = sys.argv[1]
        if scenario_key in ALL_SCENARIOS:
            scenario = ALL_SCENARIOS[scenario_key]
            connectors_config = scenario['connectors']
            
            # Filter by connector names if provided
            if len(sys.argv) > 2:
                selected_names = sys.argv[2:]
                connectors_config = {
                    k: v for k, v in connectors_config.items()
                    if k in selected_names
                }
            
            print(f"\n[+] Scenario: {scenario['name']}")
            print(f"[+] Running {len(connectors_config)} connector(s)...\n")
            run_all_connectors_parallel(connectors_config)
            return
        else:
            print(f"Unknown scenario: {scenario_key}")
            print("Available scenarios: 1-5")
            return
    
    # Interactive mode
    while True:
        scenario_choice = show_scenario_menu()
        
        if scenario_choice == "7":
            print("\n[*] Exiting...\n")
            break
        
        if scenario_choice == "6":
            # Custom scenario
            print("\n[*] Custom scenario support coming soon!")
            print("[*] For now, use environment variables to override defaults:")
            print("    export SPLUNK_HOST=your_splunk:8089")
            print("    export KAFKA_BROKERS=broker1:9092,broker2:9092")
            continue
        
        if scenario_choice in ALL_SCENARIOS:
            scenario = ALL_SCENARIOS[scenario_choice]
            
            connectors_config, selection_type = show_connector_menu(scenario)
            
            if connectors_config:
                if len(connectors_config) == 1:
                    # Single connector
                    connector_name, config = list(connectors_config.items())[0]
                    run_connector(connector_name, config)
                else:
                    # Multiple connectors
                    run_all_connectors_parallel(connectors_config)
        else:
            print("\n[-] Invalid scenario selection")

if __name__ == "__main__":
    main()
