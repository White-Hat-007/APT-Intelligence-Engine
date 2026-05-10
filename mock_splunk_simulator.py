#!/usr/bin/env python3
"""
Mock Splunk Simulator - Simulates a Splunk instance with security events
Provides search results compatible with splunk-sdk
"""

import json
import time
import socket
from threading import Thread

class MockSplunkSimulator:
    """Simulates a Splunk instance responding to searches"""
    
    def __init__(self, host='localhost', port=8089):
        self.host = host
        self.port = port
        self.search_results = [
            {
                "_time": "2026-02-27T10:15:30Z",
                "host": "WORKSTATION-01",
                "source": "WinEventLog:Security",
                "sourcetype": "WinEventLog",
                "event_id": 4688,
                "user": "DOMAIN\\Admin",
                "process": "powershell.exe",
                "command_line": "C:\\Windows\\System32\\powershell.exe -NoProfile",
                "technique": "T1086",
                "severity": "high"
            },
            {
                "_time": "2026-02-27T10:15:31Z",
                "host": "WORKSTATION-01",
                "source": "network",
                "sourcetype": "suricata",
                "src_ip": "192.168.1.100",
                "dest_ip": "192.0.2.50",
                "dest_port": 443,
                "alert": "Suspicious C2 Communication",
                "technique": "T1071",
                "severity": "critical"
            },
            {
                "_time": "2026-02-27T10:15:32Z",
                "host": "WORKSTATION-02",
                "source": "WinEventLog:Security",
                "sourcetype": "WinEventLog",
                "event_id": 4698,
                "user": "DOMAIN\\Admin",
                "task_name": "UpdateChecker",
                "command": "%windir%\\System32\\cmd.exe /c malware.bat",
                "technique": "T1053",
                "severity": "critical"
            },
            {
                "_time": "2026-02-27T10:15:33Z",
                "host": "DOMAIN-CONTROLLER",
                "source": "WinEventLog:Security",
                "sourcetype": "WinEventLog",
                "event_id": 4624,
                "user": "DOMAIN\\JohnDoe",
                "logon_type": 3,
                "source_ip": "192.168.2.50",
                "status": "Success",
                "technique": "T1078",
                "severity": "medium"
            },
            {
                "_time": "2026-02-27T10:15:34Z",
                "host": "WORKSTATION-03",
                "source": "WinEventLog:Security",
                "sourcetype": "WinEventLog",
                "event_id": 4672,
                "user": "DOMAIN\\SuspiciousUser",
                "process": "cmd.exe",
                "privilege_list": "SeBackupPrivilege, SeRestorePrivilege",
                "technique": "T1134",
                "severity": "high"
            }
        ]
        self.queries_served = 0
    
    def run(self):
        """Run the mock Splunk server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"[mock-splunk] Starting Mock Splunk Instance")
            print(f"[mock-splunk] Listening on {self.host}:{self.port}")
            print(f"[mock-splunk] Ready to serve search results\n")
            
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"[mock-splunk] Connection from {addr}")
                    client_thread = Thread(
                        target=self._handle_search,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[mock-splunk] Error: {e}")
        
        except KeyboardInterrupt:
            print(f"\n[mock-splunk] Shutting down...")
        finally:
            server_socket.close()
    
    def _handle_search(self, client_socket, addr):
        """Simulate search result responses"""
        try:
            # Receive search request (simplified)
            data = client_socket.recv(1024)
            print(f"[mock-splunk] Search request from {addr}")
            
            # Send results as JSON
            response = {
                "preview": False,
                "offset": 0,
                "results": self.search_results,
                "result_count": len(self.search_results)
            }
            
            response_json = json.dumps(response)
            client_socket.send(response_json.encode())
            print(f"[mock-splunk] Sent {len(self.search_results)} results to {addr}")
            
            self.queries_served += 1
            
        except Exception as e:
            print(f"[mock-splunk] Error handling search: {e}")
        finally:
            client_socket.close()


if __name__ == '__main__':
    simulator = MockSplunkSimulator('localhost', 8089)
    simulator.run()
