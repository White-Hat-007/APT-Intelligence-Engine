#!/usr/bin/env python3
"""
Connector Demo - Real-World Data Source Showcase

This script demonstrates all 7 connectors with their configurations.
Shows what each connector does and their connection status.
"""

import sys
import json
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colors
init(autoreset=True)

# Import configurations from main
from main import CONNECTOR_CONFIG, REALTIME_BATCH_SIZE, REALTIME_TIME_WINDOW


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}{Style.RESET_ALL}\n")


def print_connector_info(name, description, config, deps, performance):
    """Print detailed connector information."""
    print(f"{Fore.GREEN}{Style.BRIGHT}[{name.upper()}]{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Description:{Style.RESET_ALL} {description}")
    print(f"  {Fore.YELLOW}Dependencies:{Style.RESET_ALL} {deps}")
    print(f"  {Fore.YELLOW}Performance:{Style.RESET_ALL} {performance}")
    print(f"  {Fore.YELLOW}Configuration:{Style.RESET_ALL}")
    print(f"    {json.dumps(config, indent=6)}")
    print()


def show_all_connectors():
    """Display all available connectors with details."""
    print_header("ALL REAL-WORLD DATA CONNECTORS")

    connectors_info = {
        "kafka": {
            "description": "Apache Kafka message broker streaming",
            "deps": "pip install kafka-python",
            "performance": "10k-100k events/second (Excellent)",
            "use_cases": [
                "High-volume event streaming",
                "Multi-datacenter event distribution",
                "Real-time threat feeds from multiple sources",
            ]
        },
        "websocket": {
            "description": "Real-time WebSocket event endpoints",
            "deps": "pip install websocket-client",
            "performance": "1k-10k events/second (Very Good)",
            "use_cases": [
                "Live event feeds from APIs",
                "Browser-based SIEM dashboards",
                "Real-time notification systems",
            ]
        },
        "rest": {
            "description": "HTTP REST API polling",
            "deps": "pip install requests",
            "performance": "100-1k events/second (Good)",
            "use_cases": [
                "Cloud SIEM platforms",
                "REST API endpoints",
                "HTTP-based log aggregators",
            ]
        },
        "splunk": {
            "description": "Splunk Enterprise SIEM integration",
            "deps": "pip install splunk-sdk",
            "performance": "100-1k events/second (Good)",
            "use_cases": [
                "Splunk Enterprise instances",
                "Splunk Cloud deployments",
                "Saved searches and alerts",
            ]
        },
        "elastic": {
            "description": "Elasticsearch/ELK Stack integration",
            "deps": "pip install elasticsearch",
            "performance": "1k-10k events/second (Very Good)",
            "use_cases": [
                "Elastic Cloud deployments",
                "Self-hosted ELK stacks",
                "Kibana-based analytics",
            ]
        },
        "syslog": {
            "description": "RFC 3164 Syslog protocol listener",
            "deps": "None (standard library only!)",
            "performance": "1k-10k events/second (Excellent)",
            "use_cases": [
                "Network device logs (routers, firewalls)",
                "Traditional syslog servers",
                "Legacy log forwarding",
            ]
        },
        "windows_eventlog": {
            "description": "Live Windows Event Log streaming",
            "deps": "pip install pywin32 (Windows only)",
            "performance": "100-1k events/second (Good)",
            "use_cases": [
                "Windows system event monitoring",
                "Security event log analysis",
                "Application event streaming",
            ]
        },
    }

    for connector_name, info in connectors_info.items():
        config = CONNECTOR_CONFIG.get(connector_name, {})
        print_connector_info(
            connector_name,
            info["description"],
            config,
            info["deps"],
            info["performance"]
        )
        print(f"  {Fore.CYAN}Use Cases:{Style.RESET_ALL}")
        for use_case in info["use_cases"]:
            print(f"    • {use_case}")
        print()


def show_connector_comparison():
    """Show side-by-side connector comparison."""
    print_header("CONNECTOR COMPARISON MATRIX")

    data = [
        ("Connector", "Type", "Speed", "Scale", "Native Deps"),
        ("-" * 20, "-" * 15, "-" * 15, "-" * 15, "-" * 15),
        ("kafka", "Stream", "⚡⚡⚡", "Huge", "❌"),
        ("websocket", "Stream", "⚡⚡", "Large", "❌"),
        ("rest", "Stream", "⚡", "Medium", "❌"),
        ("splunk", "Stream", "⚡", "Large", "❌"),
        ("elastic", "Stream", "⚡⚡", "Huge", "❌"),
        ("syslog", "Stream", "⚡⚡⚡", "Large", "✅"),
        ("windows_eventlog", "Stream", "⚡", "Medium", "❌"),
    ]

    for row in data:
        print(f"  {row[0]:<20} {row[1]:<15} {row[2]:<15} {row[3]:<15} {row[4]:<15}")

    print(f"\n  {Fore.YELLOW}Legend:{Style.RESET_ALL}")
    print(f"    ⚡ = 100-1k evt/s  |  ⚡⚡ = 1k-10k evt/s  |  ⚡⚡⚡ = 10k-100k evt/s")
    print(f"    ✅ = No external dependencies  |  ❌ = External package required")


def show_setup_instructions():
    """Show how to set up and run connectors."""
    print_header("QUICK START - HOW TO CONFIGURE & RUN")

    print(f"{Fore.GREEN}{Style.BRIGHT}STEP 1: Install Dependencies{Style.RESET_ALL}")
    print(f"  For Kafka:         pip install kafka-python")
    print(f"  For WebSocket:     pip install websocket-client")
    print(f"  For REST:          pip install requests")
    print(f"  For Splunk:        pip install splunk-sdk")
    print(f"  For Elasticsearch: pip install elasticsearch")
    print(f"  For Windows Log:   pip install pywin32")
    print(f"  For Syslog:        (No install needed!)")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}STEP 2: Edit main.py{Style.RESET_ALL}")
    print(f"  Change line 46:")
    print(f"    MODE = \"kafka\"  # Change to your connector")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}STEP 3: Configure Your Source{Style.RESET_ALL}")
    print(f"  Edit CONNECTOR_CONFIG[\"kafka\"] in main.py with your actual settings:")
    print(f"    - Replace 'kafka:9092' with your Kafka broker")
    print(f"    - Replace 'splunk.local:8089' with your Splunk host")
    print(f"    - etc.")

    print(f"\n{Fore.GREEN}{Style.BRIGHT}STEP 4: Run{Style.RESET_ALL}")
    print(f"  python main.py")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}BATCH CONFIGURATION (All Modes):{Style.RESET_ALL}")
    print(f"  REALTIME_BATCH_SIZE = {REALTIME_BATCH_SIZE}     # Process every N events")
    print(f"  REALTIME_TIME_WINDOW = {REALTIME_TIME_WINDOW}  # OR every N seconds")
    print(f"  Trigger = whichever comes first")


def show_example_commands():
    """Show example commands for each connector."""
    print_header("EXAMPLE COMMANDS FOR EACH CONNECTOR")

    examples = {
        "kafka": "python main.py  # With MODE='kafka' and broker at kafka:9092",
        "websocket": "python main.py  # With MODE='websocket' and WS endpoint",
        "rest": "python main.py  # With MODE='rest' and API endpoint",
        "splunk": "python main.py  # With MODE='splunk' and Splunk credentials",
        "elastic": "python main.py  # With MODE='elastic' and ES host",
        "syslog": "python main.py  # With MODE='syslog' (listens on 0.0.0.0:514)",
        "windows_eventlog": "python main.py  # With MODE='windows_eventlog' (Windows only)",
    }

    for connector, command in examples.items():
        print(f"{Fore.YELLOW}{connector.upper()}:{Style.RESET_ALL}")
        print(f"  {command}")
        if connector == "syslog":
            print(f"  Send test: logger -h localhost -P 514 'test event'")
        elif connector == "kafka":
            print(f"  Requires: Kafka broker running and topic 'security_events'")
        elif connector == "splunk":
            print(f"  Requires: Splunk instance with SPL query capability")
        elif connector == "elastic":
            print(f"  Requires: Elasticsearch with index matching pattern")
        print()


def show_configuration_details():
    """Show all configurations in detail."""
    print_header("DETAILED CONFIGURATIONS (EDIT THESE IN main.py)")

    for connector_name, config in CONNECTOR_CONFIG.items():
        print(f"{Fore.GREEN}{Style.BRIGHT}{connector_name.upper()}{Style.RESET_ALL}")
        print(f"  {json.dumps(config, indent=2)}")
        print()


def interactive_menu():
    """Show interactive menu."""
    while True:
        print_header("CONNECTOR DEMO MENU")
        print(f"{Fore.CYAN}What would you like to see?{Style.RESET_ALL}\n")
        print(f"1) {Fore.YELLOW}Show all connectors{Style.RESET_ALL}")
        print(f"2) {Fore.YELLOW}Connector comparison matrix{Style.RESET_ALL}")
        print(f"3) {Fore.YELLOW}Setup instructions{Style.RESET_ALL}")
        print(f"4) {Fore.YELLOW}Example commands{Style.RESET_ALL}")
        print(f"5) {Fore.YELLOW}All configurations{Style.RESET_ALL}")
        print(f"6) {Fore.YELLOW}Run connector (interactive){Style.RESET_ALL}")
        print(f"7) {Fore.RED}Exit{Style.RESET_ALL}")
        print()

        choice = input(f"{Fore.CYAN}Enter choice (1-7): {Style.RESET_ALL}").strip()

        if choice == "1":
            show_all_connectors()
        elif choice == "2":
            show_connector_comparison()
        elif choice == "3":
            show_setup_instructions()
        elif choice == "4":
            show_example_commands()
        elif choice == "5":
            show_configuration_details()
        elif choice == "6":
            run_connector_interactive()
        elif choice == "7":
            print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}\n")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Try again.{Style.RESET_ALL}")

        input(f"\n{Fore.CYAN}Press Enter to continue...{Style.RESET_ALL}")
        print("\n" * 2)


def run_connector_interactive():
    """Interactive connector runner."""
    print_header("SELECT CONNECTOR TO RUN")

    connectors = list(CONNECTOR_CONFIG.keys())
    for i, connector in enumerate(connectors, 1):
        print(f"{i}) {connector}")
    print(f"{len(connectors) + 1}) Cancel")

    choice = input(f"\n{Fore.CYAN}Select connector (1-{len(connectors) + 1}): {Style.RESET_ALL}").strip()

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(connectors):
            print(f"{Fore.RED}Invalid selection.{Style.RESET_ALL}")
            return

        selected = connectors[idx]
        print(f"\n{Fore.GREEN}Selected: {selected}{Style.RESET_ALL}")
        print(f"\nTo run this connector:")
        print(f"  1. Edit main.py line 46:")
        print(f"     MODE = \"{selected}\"")
        print(f"  2. Configure CONNECTOR_CONFIG[\"{selected}\"] with your settings")
        print(f"  3. Run: python main.py")

    except ValueError:
        print(f"{Fore.RED}Invalid input.{Style.RESET_ALL}")


def main():
    """Main entry point."""
    print_header("🔌 REAL-WORLD DATA CONNECTORS DEMO")

    print(f"{Fore.GREEN}{Style.BRIGHT}Available Connectors:{Style.RESET_ALL}")
    for i, connector in enumerate(CONNECTOR_CONFIG.keys(), 1):
        print(f"  {i}. {connector}")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Quick Info:{Style.RESET_ALL}")
    print(f"  • 7 production-ready connectors")
    print(f"  • Support for enterprise data sources")
    print(f"  • Configurable batch processing")
    print(f"  • Thread-safe real-time ingestion")
    print(f"  • Security-first design")

    print(f"\n{Fore.YELLOW}Choose an option:{Style.RESET_ALL}")
    print(f"  1) Interactive menu")
    print(f"  2) Show all connectors")
    print(f"  3) Show comparison matrix")
    print(f"  4) Show setup instructions")
    print(f"  5) Show all configurations")
    choice = input(f"\n{Fore.CYAN}Enter (1-5) or 'q' to quit: {Style.RESET_ALL}").strip().lower()

    if choice == "1":
        interactive_menu()
    elif choice == "2":
        show_all_connectors()
    elif choice == "3":
        show_connector_comparison()
    elif choice == "4":
        show_setup_instructions()
    elif choice == "5":
        show_configuration_details()
    elif choice == "q":
        print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}Invalid choice.{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted.{Style.RESET_ALL}\n")
        sys.exit(0)
