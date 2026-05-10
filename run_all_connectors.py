#!/usr/bin/env python3
"""
Multi-Connector Orchestrator
Runs all 7 connectors simultaneously in parallel threads with real-time monitoring
"""

import threading
import time
import sys
import os
from collections import defaultdict
from datetime import datetime
from ingestion.realtime_ingestor import RealTimeIngestor
from ingestion.connectors import get_connector

# Enable UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Configuration for all connectors
CONNECTORS_TO_RUN = {
    "kafka": {
        "config": {
            "topic": "security_events",
            "bootstrap_servers": ["localhost:9092"]
        },
        "description": "Apache Kafka Message Broker"
    },
    "websocket": {
        "config": {
            "url": "wss://localhost:8080/events",
            "max_retries": 3
        },
        "description": "WebSocket Real-Time Events"
    },
    "rest": {
        "config": {
            "api_url": "https://api.localhost/events",
            "poll_interval": 5.0,
            "auth_token": "bearer_token_here"
        },
        "description": "REST API Polling"
    },
    "splunk": {
        "config": {
            "host": "localhost:8089",
            "username": "admin",
            "password": "password",
            "search_query": "sourcetype=sysmon EventCode=1"
        },
        "description": "Splunk Enterprise"
    },
    "elastic": {
        "config": {
            "hosts": ["localhost:9200"],
            "index_pattern": "logs-sysmon-*",
            "query": {"match_all": {}}
        },
        "description": "Elasticsearch / ELK Stack"
    },
    "syslog": {
        "config": {
            "host": "0.0.0.0",
            "port": 514,
            "protocol": "udp"
        },
        "description": "Syslog (RFC 3164) - NO DEPENDENCIES!"
    },
    "windows_eventlog": {
        "config": {
            "log_name": "Security"
        },
        "description": "Windows Event Log (Windows only)"
    }
}

class ConnectorStats:
    """Track statistics for each connector"""
    def __init__(self):
        self.events_received = 0
        self.batches_processed = 0
        self.errors = 0
        self.last_event_time = None
        self.status = "initializing"
        self.lock = threading.Lock()
    
    def record_event(self):
        with self.lock:
            self.events_received += 1
            self.last_event_time = datetime.now()
    
    def record_batch(self):
        with self.lock:
            self.batches_processed += 1
    
    def record_error(self):
        with self.lock:
            self.errors += 1
    
    def update_status(self, status):
        with self.lock:
            self.status = status

class MultiConnectorOrchestrator:
    """Runs multiple connectors in parallel with monitoring"""
    
    def __init__(self, batch_size=10, time_window=3):
        self.batch_size = batch_size
        self.time_window = time_window
        self.connectors = {}
        self.stats = defaultdict(ConnectorStats)
        self.threads = {}
        self.running = False
        self.lock = threading.Lock()
    
    def start_connector(self, connector_name, config):
        """Start a single connector in a thread"""
        def run_connector():
            try:
                self.stats[connector_name].update_status("connecting")
                print(f"{Colors.YELLOW}[{connector_name}]{Colors.ENDC} Starting connector...")
                
                # Get connector
                try:
                    event_stream = get_connector(connector_name, **config)
                except TypeError:
                    # Handle case where connector doesn't need kwargs
                    event_stream = get_connector(connector_name)
                
                self.stats[connector_name].update_status("running")
                print(f"{Colors.GREEN}[{connector_name}]{Colors.ENDC} Connected! Processing events...")
                
                event_count = 0
                try:
                    for event in event_stream:
                        if not self.running:
                            break
                        
                        self.stats[connector_name].record_event()
                        event_count += 1
                        
                        # Show event info every 10 events
                        if event_count % 10 == 0:
                            timestamp = event.get("timestamp", "N/A")
                            host = event.get("host", "N/A")
                            technique = event.get("technique_id", "N/A")
                            print(f"{Colors.CYAN}[{connector_name}]{Colors.ENDC} Event #{event_count}: {host} | {technique} | {timestamp}")
                        
                        # Record batch every N events
                        if event_count % self.batch_size == 0:
                            self.stats[connector_name].record_batch()
                            print(f"{Colors.BLUE}[{connector_name}]{Colors.ENDC} Batch #{self.stats[connector_name].batches_processed} processed ({self.batch_size} events)")
                
                except StopIteration:
                    self.stats[connector_name].update_status("completed")
                    print(f"{Colors.GREEN}[{connector_name}]{Colors.ENDC} Stream completed")
                except Exception as e:
                    self.stats[connector_name].record_error()
                    self.stats[connector_name].update_status(f"error: {type(e).__name__}")
                    print(f"{Colors.RED}[{connector_name}]{Colors.ENDC} Error: {e}")
            
            except Exception as e:
                self.stats[connector_name].record_error()
                self.stats[connector_name].update_status("failed")
                print(f"{Colors.RED}[{connector_name}]{Colors.ENDC} Failed to connect: {e}")
        
        thread = threading.Thread(target=run_connector, daemon=True, name=f"connector-{connector_name}")
        self.threads[connector_name] = thread
        thread.start()
    
    def start_all(self):
        """Start all connectors simultaneously"""
        self.running = True
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}>> MULTI-CONNECTOR ORCHESTRATOR - ALL 7 CONNECTORS STARTING{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}\n{Colors.ENDC}")
        
        for connector_name, info in CONNECTORS_TO_RUN.items():
            print(f"{Colors.YELLOW}→ Starting {connector_name}: {info['description']}{Colors.ENDC}")
            self.start_connector(connector_name, info['config'])
            time.sleep(0.5)  # Stagger starts
        
        print(f"\n{Colors.GREEN}[OK] All {len(CONNECTORS_TO_RUN)} connectors started!{Colors.ENDC}\n")
    
    def stop_all(self):
        """Stop all connectors"""
        self.running = False
        for thread in self.threads.values():
            thread.join(timeout=2)
    
    def print_statistics(self):
        """Print real-time statistics for all connectors"""
        while self.running:
            time.sleep(5)
            print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.GREEN}[STATS] CONNECTOR STATISTICS{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
            print(f"{'Connector':<18} {'Status':<15} {'Events':<10} {'Batches':<10} {'Errors':<8}")
            print(f"{Colors.CYAN}{'-'*80}{Colors.ENDC}")
            
            for connector_name, stats in sorted(self.stats.items()):
                status = stats.status
                if status == "running":
                    status_color = Colors.GREEN
                elif status == "connecting":
                    status_color = Colors.YELLOW
                elif "error" in status:
                    status_color = Colors.RED
                else:
                    status_color = Colors.CYAN
                
                print(f"{connector_name:<18} "
                      f"{status_color}{status:<15}{Colors.ENDC} "
                      f"{stats.events_received:<10} "
                      f"{stats.batches_processed:<10} "
                      f"{stats.errors:<8}")
            
            print(f"{Colors.CYAN}{'-'*80}{Colors.ENDC}")

def main():
    """Main entry point"""
    # Check for command line argument
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print(f"""
{Colors.BOLD}{Colors.CYAN}========================================================================{Colors.ENDC}
{Colors.BOLD}{Colors.GREEN}  APT THREAT INTELLIGENCE ENGINE{Colors.ENDC}
{Colors.BOLD}{Colors.GREEN}  ALL CONNECTORS - SIMULTANEOUS EXECUTION{Colors.ENDC}
{Colors.BOLD}{Colors.CYAN}========================================================================{Colors.ENDC}

{Colors.YELLOW}Choose mode:{Colors.ENDC}
  1) Run ALL 7 connectors simultaneously
  2) Run only SYSLOG (no external dependencies)
  3) Run only KAFKA
  4) Run interactive selection

Option (1-4): """, end="")
        
        choice = input().strip() or "1"
    
    orchestrator = MultiConnectorOrchestrator(batch_size=10, time_window=3)
    
    if choice == "1":
        connectors_to_run = CONNECTORS_TO_RUN
    elif choice == "2":
        connectors_to_run = {"syslog": CONNECTORS_TO_RUN["syslog"]}
    elif choice == "3":
        connectors_to_run = {"kafka": CONNECTORS_TO_RUN["kafka"]}
    elif choice == "4":
        print(f"\n{Colors.YELLOW}Available connectors:{Colors.ENDC}")
        for i, name in enumerate(CONNECTORS_TO_RUN.keys(), 1):
            desc = CONNECTORS_TO_RUN[name]["description"]
            print(f"  {i}) {name:<18} - {desc}")
        print(f"  8) All connectors")
        
        selections = input(f"\n{Colors.YELLOW}Enter connector numbers (comma-separated): {Colors.ENDC}").strip()
        
        if selections == "8":
            connectors_to_run = CONNECTORS_TO_RUN
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selections.split(",")]
                connector_names = list(CONNECTORS_TO_RUN.keys())
                connectors_to_run = {
                    connector_names[i]: CONNECTORS_TO_RUN[connector_names[i]]
                    for i in indices if 0 <= i < len(connector_names)
                }
            except:
                print(f"{Colors.RED}Invalid selection. Running all.{Colors.ENDC}")
                connectors_to_run = CONNECTORS_TO_RUN
    else:
        connectors_to_run = CONNECTORS_TO_RUN
    
    # Filter by connectors to run
    FILTERED_CONNECTORS = connectors_to_run
    
    try:
        # Start all selected connectors
        orchestrator.start_all()
        
        # Print statistics periodically
        stats_thread = threading.Thread(
            target=orchestrator.print_statistics,
            daemon=True,
            name="statistics"
        )
        stats_thread.start()
        
        # Keep running until interrupted
        print(f"{Colors.YELLOW}Press Ctrl+C to stop all connectors...{Colors.ENDC}\n")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Shutting down all connectors...{Colors.ENDC}")
        orchestrator.stop_all()
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}[FINAL] STATISTICS{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
        print(f"{'Connector':<18} {'Status':<15} {'Events':<10} {'Batches':<10} {'Errors':<8}")
        print(f"{Colors.CYAN}{'-'*80}{Colors.ENDC}")
        
        total_events = 0
        total_batches = 0
        total_errors = 0
        
        for connector_name, stats in sorted(orchestrator.stats.items()):
            total_events += stats.events_received
            total_batches += stats.batches_processed
            total_errors += stats.errors
            
            status_color = Colors.RED if stats.errors > 0 else Colors.GREEN
            print(f"{connector_name:<18} "
                  f"{status_color}{stats.status:<15}{Colors.ENDC} "
                  f"{stats.events_received:<10} "
                  f"{stats.batches_processed:<10} "
                  f"{stats.errors:<8}")
        
        print(f"{Colors.CYAN}{'-'*80}{Colors.ENDC}")
        print(f"{'TOTAL':<18} {'':<15} {total_events:<10} {total_batches:<10} {total_errors:<8}")
        print(f"{Colors.CYAN}{'='*80}{Colors.ENDC}\n")
        
        print(f"{Colors.GREEN}[OK] All connectors stopped gracefully{Colors.ENDC}\n")

if __name__ == "__main__":
    main()
