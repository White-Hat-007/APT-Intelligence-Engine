#!/usr/bin/env python3
"""
Mock WebSocket Server - Simulates real-time threat alert stream
Broadcasts security events to connected clients
"""

import json
import time
import asyncio
import ssl
from threading import Thread
import socket

# Security alerts to broadcast
SECURITY_ALERTS = [
    {
        "alert_id": "alert-001",
        "timestamp": "2026-02-27T10:15:30Z",
        "severity": "CRITICAL",
        "title": "Suspicious PowerShell Execution Detected",
        "description": "Unusual PowerShell execution with obfuscated commands",
        "source": "Endpoint Detection",
        "techniques": ["T1086", "T1059"],
        "affected_host": "WORKSTATION-01"
    },
    {
        "alert_id": "alert-002",
        "timestamp": "2026-02-27T10:15:35Z",
        "severity": "HIGH",
        "title": "Data Exfiltration Attempt",
        "description": "Outbound connection to known malware C2 server",
        "source": "Network Detection",
        "techniques": ["T1071", "T1041"],
        "affected_host": "WORKSTATION-01"
    },
    {
        "alert_id": "alert-003",
        "timestamp": "2026-02-27T10:15:40Z",
        "severity": "CRITICAL",
        "title": "Lateral Movement Detected",
        "description": "Credential usage from unexpected source",
        "source": "Identity Detection",
        "techniques": ["T1078", "T1570"],
        "affected_host": "DOMAIN-CONTROLLER"
    },
    {
        "alert_id": "alert-004",
        "timestamp": "2026-02-27T10:15:45Z",
        "severity": "MEDIUM",
        "title": "Registry Persistence Mechanism",
        "description": "Suspicious registry modification for persistence",
        "source": "Endpoint Detection",
        "techniques": ["T1547", "T1112"],
        "affected_host": "WORKSTATION-02"
    }
]

# Simple TCP-based WebSocket server (avoiding complex ws library)
class SimpleWebSocketServer:
    def __init__(self, host='localhost', port=8443):
        self.host = host
        self.port = port
        self.alerts_sent = 0
    
    def run(self):
        """Run the WebSocket server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"[mock-websocket] Starting Mock WebSocket Server")
            print(f"[mock-websocket] Listening on wss://{self.host}:{self.port}/stream")
            print(f"[mock-websocket] Broadcasting threat alerts...\n")
            
            # Broadcast alerts to clients
            client_threads = []
            broadcast_thread = Thread(target=self._broadcast_alerts, daemon=True)
            broadcast_thread.start()
            
            # Accept connections
            connection_count = 0
            while True:
                try:
                    client_socket, addr = server_socket.accept()
                    connection_count += 1
                    print(f"[mock-websocket] Client connected: {addr} (connection #{connection_count})")
                    
                    client_thread = Thread(
                        target=self._handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    client_threads.append(client_thread)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[mock-websocket] Connection error: {e}")
        
        except KeyboardInterrupt:
            print(f"\n[mock-websocket] Shutting down...")
        finally:
            server_socket.close()
    
    def _handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        try:
            # Send WebSocket handshake response (simplified)
            handshake_response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Accept: dummy\r\n"
                "\r\n"
            )
            client_socket.send(handshake_response.encode())
            print(f"[mock-websocket] Client {addr} handshake complete")
            
            # Keep connection alive and send alerts
            while True:
                time.sleep(3)
                # In real WebSocket, would send binary frames
                # For now, just keep connection alive
                
        except Exception as e:
            print(f"[mock-websocket] Client {addr} disconnected: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _broadcast_alerts(self):
        """Continuously broadcast alerts"""
        alert_index = 0
        while True:
            try:
                alert = SECURITY_ALERTS[alert_index % len(SECURITY_ALERTS)]
                self.alerts_sent += 1
                print(f"[mock-websocket] Broadcasting alert: {alert['title']}")
                alert_index += 1
                time.sleep(5)  # Send new alert every 5 seconds
            except Exception as e:
                print(f"[mock-websocket] Broadcast error: {e}")
                time.sleep(5)


if __name__ == '__main__':
    server = SimpleWebSocketServer('localhost', 8443)
    server.run()
