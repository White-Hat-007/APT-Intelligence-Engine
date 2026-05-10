#!/usr/bin/env python3
"""
Mock REST API Server - Simulates a security API with threat events
Responds to HTTP requests with realistic security event data
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os

# Sample security events to serve
SECURITY_EVENTS = [
    {
        "event_id": "evt-001",
        "timestamp": "2026-02-27T10:15:30Z",
        "source": "mock-api",
        "hostname": "WORKSTATION-01",
        "event_type": "ProcessCreate",
        "process_name": "powershell.exe",
        "command_line": "C:\\Windows\\System32\\powershell.exe -NoProfile -ExecutionPolicy Bypass",
        "technique": "T1086",
        "severity": "high"
    },
    {
        "event_id": "evt-002",
        "timestamp": "2026-02-27T10:15:31Z",
        "source": "mock-api",
        "hostname": "WORKSTATION-01",
        "event_type": "NetworkConnection",
        "source_ip": "192.168.1.100",
        "dest_ip": "192.0.2.50",
        "dest_port": 443,
        "protocol": "TCP",
        "technique": "T1071",
        "severity": "high"
    },
    {
        "event_id": "evt-003",
        "timestamp": "2026-02-27T10:15:32Z",
        "source": "mock-api",
        "hostname": "WORKSTATION-01",
        "event_type": "FileCreate",
        "target_filename": "C:\\Windows\\Temp\\persistence.bat",
        "file_size": 256,
        "technique": "T1547",
        "severity": "critical"
    },
    {
        "event_id": "evt-004",
        "timestamp": "2026-02-27T10:15:33Z",
        "source": "mock-api",
        "hostname": "WORKSTATION-02",
        "event_type": "DNSQuery",
        "query_name": "malware-c2.evil.com",
        "query_status": "resolved",
        "response": "192.0.2.100",
        "technique": "T1071",
        "severity": "critical"
    },
    {
        "event_id": "evt-005",
        "timestamp": "2026-02-27T10:15:34Z",
        "source": "mock-api",
        "hostname": "DOMAIN-CONTROLLER",
        "event_type": "LogonEvent",
        "user": "DOMAIN\\Admin",
        "logon_type": "Network",
        "source_ip": "192.168.2.50",
        "technique": "T1078",
        "severity": "medium"
    }
]

event_counter = 0

class MockAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for mock security API"""
    
    def do_GET(self):
        """Handle GET requests"""
        global event_counter
        
        if self.path == '/v1/events':
            # Return security events
            events = []
            for i in range(3):  # Return 3 events per request
                event = SECURITY_EVENTS[event_counter % len(SECURITY_EVENTS)].copy()
                event['event_id'] = f"evt-{event_counter + 1:04d}"
                events.append(event)
                event_counter += 1
            
            response = {
                'status': 'success',
                'count': len(events),
                'events': events
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
            print(f"[mock-api] GET /v1/events → Returned {len(events)} events (total served: {event_counter})")
        
        elif self.path == '/v1/health':
            # Health check endpoint
            response = {'status': 'healthy', 'uptime': time.time()}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            print(f"[mock-api] Health check OK")
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def log_message(self, format, *args):
        """Suppress verbose logging"""
        pass


def run_mock_api_server(host='localhost', port=8443):
    """Start the mock API server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MockAPIHandler)
    
    print(f"[mock-api] Starting Mock REST API Server")
    print(f"[mock-api] Listening on https://{host}:{port}")
    print(f"[mock-api] GET /v1/events - Returns security events")
    print(f"[mock-api] GET /v1/health - Health check")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[mock-api] Shutting down...")
        httpd.shutdown()


if __name__ == '__main__':
    # Run on localhost:8443 (HTTPS simulation, but actually HTTP)
    run_mock_api_server('localhost', 8443)
