"""
Real-World Event Source Connectors

Provides pluggable generators for various telemetry sources:
- Kafka
- WebSocket
- REST API
- Splunk
- Elastic/ELK
- Syslog
- Windows Event Log

All return standardized event dictionaries compatible with RealTimeIngestor.
"""

import json
import time
import uuid
import socket
import struct
from datetime import datetime, timezone
from typing import Generator, Dict, Any, Optional, List


# ==========================================
# KAFKA CONNECTOR
# ==========================================

def kafka_event_stream(
    topic: str,
    bootstrap_servers: List[str],
    group_id: str = "threat-intelligence-engine",
    auto_offset_reset: str = "earliest",
    max_retries: int = 3,
    timeout_seconds: float = 10.0,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream events from Apache Kafka topic.
    
    Args:
        topic: Kafka topic name
        bootstrap_servers: List of bootstrap server addresses (e.g., ['localhost:9092'])
        group_id: Consumer group ID
        auto_offset_reset: 'earliest' or 'latest'
        max_retries: Retry attempts on connection failure
        timeout_seconds: Consumer timeout
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install kafka-python
    
    Example:
        source = kafka_event_stream(
            topic="security_events",
            bootstrap_servers=["kafka1:9092", "kafka2:9092"]
        )
        for event in source:
            print(event)
    """
    try:
        from kafka import KafkaConsumer
        from kafka.errors import KafkaError
    except ImportError:
        raise ImportError(
            "kafka-python is required. Install with: pip install kafka-python"
        )
    
    consumer = None
    retries = 0
    
    while retries < max_retries:
        try:
            print(f"[Kafka] Connecting to {bootstrap_servers}...")
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                consumer_timeout_ms=int(timeout_seconds * 1000),
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            print(f"[Kafka] Connected to topic: {topic}")
            retries = 0  # Reset on successful connection
            
            for message in consumer:
                if message is None:
                    break
                
                raw_event = message.value
                
                # Normalize to standard schema
                yield {
                    "campaign_id": raw_event.get("campaign_id", "KAFKA-STREAM"),
                    "event_id": raw_event.get("event_id", str(uuid.uuid4())),
                    "timestamp": raw_event.get("timestamp", str(datetime.now(timezone.utc))),
                    "host": raw_event.get("host", "UNKNOWN"),
                    "technique_id": raw_event.get("technique_id", None),
                    "source": "kafka",
                    "_raw": raw_event,
                }
        
        except KafkaError as e:
            retries += 1
            print(f"[Kafka] Error (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                time.sleep(2 ** retries)  # Exponential backoff
            else:
                raise
        
        except json.JSONDecodeError as e:
            print(f"[Kafka] JSON decode error: {e}, skipping message")
            continue
        
        except Exception as e:
            print(f"[Kafka] Unexpected error: {e}")
            raise
        
        finally:
            if consumer:
                consumer.close()


# ==========================================
# WEBSOCKET CONNECTOR
# ==========================================

def websocket_event_stream(
    url: str,
    max_retries: int = 3,
    reconnect_delay: float = 2.0,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream events from WebSocket endpoint.
    
    Args:
        url: WebSocket URL (e.g., 'wss://siem.local:8080/stream')
        max_retries: Reconnection attempts
        reconnect_delay: Delay between reconnection attempts
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install websocket-client
    
    Example:
        source = websocket_event_stream('wss://siem.local:8080/events')
        for event in source:
            print(event)
    """
    try:
        import websocket
    except ImportError:
        raise ImportError(
            "websocket-client is required. Install with: pip install websocket-client"
        )
    
    retries = 0
    
    while retries < max_retries:
        try:
            print(f"[WebSocket] Connecting to {url}...")
            ws = websocket.WebSocketApp(
                url,
                on_message=lambda ws, msg: None,  # Handled in loop
                on_error=lambda ws, err: print(f"[WebSocket] Error: {err}"),
                on_close=lambda ws, close_status_code, close_msg: None,
            )
            
            ws.run_forever()  # Blocking, needs thread or async
            
            # For non-blocking approach:
            ws = websocket.create_connection(url, timeout=10)
            print(f"[WebSocket] Connected to {url}")
            retries = 0
            
            while True:
                try:
                    message = ws.recv()
                    
                    if not message:
                        break
                    
                    raw_event = json.loads(message)
                    
                    yield {
                        "campaign_id": raw_event.get("campaign_id", "WS-STREAM"),
                        "event_id": raw_event.get("event_id", str(uuid.uuid4())),
                        "timestamp": raw_event.get("timestamp", str(datetime.now(timezone.utc))),
                        "host": raw_event.get("host", "UNKNOWN"),
                        "technique_id": raw_event.get("technique_id", None),
                        "source": "websocket",
                        "_raw": raw_event,
                    }
                
                except websocket.WebSocketTimeoutException:
                    print("[WebSocket] Timeout, reconnecting...")
                    break
                except json.JSONDecodeError:
                    print("[WebSocket] JSON decode error, skipping message")
                    continue
        
        except Exception as e:
            retries += 1
            print(f"[WebSocket] Connection failed (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                time.sleep(reconnect_delay)
            else:
                raise
        
        finally:
            try:
                ws.close()
            except:
                pass


# ==========================================
# REST API POLLING CONNECTOR
# ==========================================

def rest_poll_event_stream(
    api_url: str,
    poll_interval: float = 5.0,
    max_retries: int = 3,
    headers: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Poll REST API for security events.
    
    Args:
        api_url: API endpoint returning JSON array of events
        poll_interval: Seconds between polls
        max_retries: Retry attempts per request
        headers: Additional HTTP headers
        auth_token: Optional Bearer token for authentication
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install requests
    
    Example:
        source = rest_poll_event_stream(
            api_url='https://api.siem.local/api/events',
            auth_token='bearer_token_here',
            poll_interval=10.0
        )
        for event in source:
            print(event)
    """
    try:
        import requests
    except ImportError:
        raise ImportError(
            "requests is required. Install with: pip install requests"
        )
    
    if headers is None:
        headers = {}
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    headers["Content-Type"] = "application/json"
    
    session = requests.Session()
    last_event_id = None
    
    print(f"[REST API] Starting poll from {api_url} (interval: {poll_interval}s)")
    
    while True:
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                # Add filtering param if available
                params = {}
                if last_event_id:
                    params["after"] = last_event_id
                
                response = session.get(
                    api_url,
                    headers=headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                events = response.json()
                
                if not isinstance(events, list):
                    events = [events]
                
                for raw_event in events:
                    last_event_id = raw_event.get("event_id", last_event_id)
                    
                    yield {
                        "campaign_id": raw_event.get("campaign_id", "REST-STREAM"),
                        "event_id": raw_event.get("event_id", str(uuid.uuid4())),
                        "timestamp": raw_event.get("timestamp", str(datetime.now(timezone.utc))),
                        "host": raw_event.get("host", "UNKNOWN"),
                        "technique_id": raw_event.get("technique_id", None),
                        "source": "rest_api",
                        "_raw": raw_event,
                    }
                
                success = True
            
            except requests.exceptions.RequestException as e:
                retries += 1
                print(f"[REST API] Request failed (attempt {retries}/{max_retries}): {e}")
                if retries < max_retries:
                    time.sleep(2 ** retries)
                else:
                    print(f"[REST API] Max retries exceeded, waiting {poll_interval}s before retry")
            
            except json.JSONDecodeError as e:
                print(f"[REST API] JSON decode error: {e}")
                success = True
            
            except Exception as e:
                print(f"[REST API] Unexpected error: {e}")
                success = True
        
        # Wait before next poll
        time.sleep(poll_interval)


# ==========================================
# SPLUNK CONNECTOR
# ==========================================

def splunk_event_stream(
    host: str,
    username: str,
    password: str,
    search_query: str,
    app: str = "search",
    max_retries: int = 3,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream events from Splunk using saved search or query.
    
    Args:
        host: Splunk host (e.g., 'splunk.local:8089')
        username: Splunk username
        password: Splunk password
        search_query: Splunk search query (SPL)
        app: Splunk app context
        max_retries: Retry attempts
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install splunk-sdk
    
    Example:
        source = splunk_event_stream(
            host='splunk.local:8089',
            username='admin',
            password='password',
            search_query='sourcetype=sysmon EventCode=1 | fields host, process_name'
        )
        for event in source:
            print(event)
    """
    try:
        from splunk_sdk import client
    except ImportError:
        raise ImportError(
            "splunk-sdk is required. Install with: pip install splunk-sdk"
        )
    
    retries = 0
    
    while retries < max_retries:
        try:
            print(f"[Splunk] Connecting to {host}...")
            service = client.connect(
                host=host.split(':')[0],
                port=int(host.split(':')[1]) if ':' in host else 8089,
                username=username,
                password=password,
                app=app,
            )
            print(f"[Splunk] Connected. Executing search: {search_query}")
            
            # Create search job
            job = service.jobs.create(search_query)
            
            # Wait for job to complete
            while not job.is_done():
                print(f"[Splunk] Search progress: {job['progress']}%")
                time.sleep(1)
            
            print(f"[Splunk] Search complete. Processing {job.result_count} results")
            
            # Stream results
            results = job.results()
            for result in results:
                # result is a dict of field:value pairs
                raw_event = dict(result)
                
                yield {
                    "campaign_id": raw_event.get("campaign_id", "SPLUNK-SEARCH"),
                    "event_id": raw_event.get("event_id", str(uuid.uuid4())),
                    "timestamp": raw_event.get("_time", str(datetime.now(timezone.utc))),
                    "host": raw_event.get("host", raw_event.get("src", "UNKNOWN")),
                    "technique_id": raw_event.get("technique_id", None),
                    "source": "splunk",
                    "_raw": raw_event,
                }
            
            retries = 0  # Reset on success
        
        except Exception as e:
            retries += 1
            print(f"[Splunk] Error (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                time.sleep(2 ** retries)
            else:
                raise


# ==========================================
# ELASTIC/ELK CONNECTOR
# ==========================================

def elastic_event_stream(
    hosts: List[str],
    index_pattern: str,
    query: Optional[Dict[str, Any]] = None,
    scroll_time: str = "2m",
    max_retries: int = 3,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream events from Elasticsearch cluster.
    
    Args:
        hosts: List of Elasticsearch hosts (e.g., ['localhost:9200'])
        index_pattern: Index pattern to search (e.g., 'logs-*')
        query: Elasticsearch query DSL (dict), defaults to match_all
        scroll_time: Time to keep scroll context alive
        max_retries: Retry attempts
        username: Optional username for authentication
        password: Optional password for authentication
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install elasticsearch
    
    Example:
        source = elastic_event_stream(
            hosts=['elasticsearch:9200'],
            index_pattern='logs-sysmon-*',
            query={'query': {'term': {'event.category': 'process'}}}
        )
        for event in source:
            print(event)
    """
    try:
        from elasticsearch import Elasticsearch
        from elasticsearch.exceptions import ElasticsearchException
    except ImportError:
        raise ImportError(
            "elasticsearch is required. Install with: pip install elasticsearch"
        )
    
    if query is None:
        query = {'query': {'match_all': {}}}
    
    retries = 0
    
    while retries < max_retries:
        try:
            print(f"[Elastic] Connecting to {hosts}...")
            
            # Create client with optional auth
            if username and password:
                es = Elasticsearch(
                    hosts=hosts,
                    basic_auth=(username, password),
                    request_timeout=30,
                )
            else:
                es = Elasticsearch(hosts=hosts, request_timeout=30)
            
            # Test connection
            es.info()
            print(f"[Elastic] Connected. Searching index pattern: {index_pattern}")
            
            # Initialize scroll
            response = es.search(
                index=index_pattern,
                body=query,
                scroll=scroll_time,
                size=100,
            )
            
            scroll_id = response['_scroll_id']
            total_hits = response['hits']['total']['value']
            print(f"[Elastic] Found {total_hits} documents")
            
            # Stream results using scroll API
            while len(response['hits']['hits']) > 0:
                for hit in response['hits']['hits']:
                    raw_event = hit['_source']
                    
                    yield {
                        "campaign_id": raw_event.get("campaign_id", "ELASTIC-STREAM"),
                        "event_id": raw_event.get("event_id", hit['_id']),
                        "timestamp": raw_event.get("@timestamp", raw_event.get("timestamp", str(datetime.now(timezone.utc)))),
                        "host": raw_event.get("host", raw_event.get("hostname", "UNKNOWN")),
                        "technique_id": raw_event.get("technique_id", None),
                        "source": "elasticsearch",
                        "_raw": raw_event,
                    }
                
                # Get next batch
                response = es.scroll(scroll_id=scroll_id, scroll=scroll_time)
                scroll_id = response['_scroll_id']
            
            # Clean up scroll
            es.clear_scroll(scroll_id=scroll_id)
            retries = 0
        
        except ElasticsearchException as e:
            retries += 1
            print(f"[Elastic] Error (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                time.sleep(2 ** retries)
            else:
                raise
        
        except Exception as e:
            print(f"[Elastic] Unexpected error: {e}")
            raise


# ==========================================
# SYSLOG CONNECTOR
# ==========================================

def syslog_event_stream(
    host: str = "0.0.0.0",
    port: int = 514,
    protocol: str = "udp",
    buffer_size: int = 1024,
) -> Generator[Dict[str, Any], None, None]:
    """
    Listen for and stream events from Syslog source.
    
    Args:
        host: Bind address
        port: Syslog port (514 default)
        protocol: 'udp' or 'tcp'
        buffer_size: Receive buffer size
    
    Yields:
        Standardized event dictionaries
    
    Requirements: Standard library only
    
    Example:
        source = syslog_event_stream(host='0.0.0.0', port=514)
        for event in source:
            print(event)
    """
    import re
    from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
    
    print(f"[Syslog] Listening on {host}:{port} ({protocol.upper()})")
    
    sock = socket(AF_INET, SOCK_DGRAM if protocol == "udp" else SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind((host, port))
    
    if protocol == "tcp":
        sock.listen(1)
    
    try:
        while True:
            if protocol == "udp":
                data, addr = sock.recvfrom(buffer_size)
                syslog_msg = data.decode('utf-8', errors='ignore')
            else:
                conn, addr = sock.accept()
                data = conn.recv(buffer_size)
                syslog_msg = data.decode('utf-8', errors='ignore')
                conn.close()
            
            # Parse syslog format: <PRI>HOSTNAME TAG[PID]: MESSAGE
            # or: <PRI>TIMESTAMP HOSTNAME TAG: MESSAGE
            
            try:
                # Extract priority
                pri_match = re.match(r'<(\d+)>(.*)', syslog_msg)
                if pri_match:
                    pri = int(pri_match.group(1))
                    severity = pri % 8
                    facility = pri // 8
                    message = pri_match.group(2)
                else:
                    facility = 16  # local0
                    severity = 6   # info
                    message = syslog_msg
                
                # Extract hostname and tag
                parts = message.split()
                if len(parts) > 0:
                    hostname = parts[0] if not parts[0][0].isdigit() else "unknown"
                    tag = parts[1] if len(parts) > 1 else "syslog"
                else:
                    hostname = str(addr[0])
                    tag = "syslog"
                
                raw_event = {
                    "facility": facility,
                    "severity": severity,
                    "hostname": hostname,
                    "tag": tag,
                    "message": message,
                }
                
                yield {
                    "campaign_id": "SYSLOG-STREAM",
                    "event_id": str(uuid.uuid4()),
                    "timestamp": str(datetime.now(timezone.utc)),
                    "host": hostname,
                    "technique_id": None,  # Syslog doesn't have technique mapping by default
                    "source": "syslog",
                    "_raw": raw_event,
                }
            
            except Exception as e:
                print(f"[Syslog] Parse error: {e}, skipping message")
                continue
    
    except KeyboardInterrupt:
        print("[Syslog] Listener stopped")
    finally:
        sock.close()


# ==========================================
# WINDOWS EVENT LOG CONNECTOR
# ==========================================

def windows_eventlog_stream(
    log_name: str = "Security",
    max_retries: int = 3,
) -> Generator[Dict[str, Any], None, None]:
    """
    Stream events from Windows Event Log in real-time.
    
    Args:
        log_name: Event log name (Security, System, Application, etc.)
        max_retries: Retry attempts on error
    
    Yields:
        Standardized event dictionaries
    
    Requires: pip install pywin32 (Windows only)
    
    Example:
        source = windows_eventlog_stream(log_name='Security')
        for event in source:
            print(event)
    """
    try:
        import win32evtlog
        import win32security
        import win32con
    except ImportError:
        raise ImportError(
            "pywin32 is required on Windows. Install with: pip install pywin32"
        )
    
    print(f"[Windows EventLog] Monitoring {log_name} log")
    
    retries = 0
    
    while retries < max_retries:
        try:
            # Open the log
            handle = win32evtlog.OpenEventLog(None, log_name)
            flags = win32evtlog.FORWARDS_READ | win32evtlog.SEEK_READ
            
            # Get current record count
            total = win32evtlog.GetNumberOfEventLogRecords(handle)
            print(f"[Windows EventLog] Total {total} records in {log_name}")
            
            # Start from most recent
            record_id = total
            
            while True:
                try:
                    # Read events (batch)
                    events = win32evtlog.ReadEventLog(handle, flags, record_id, 10)
                    
                    if not events:
                        # Wait for new events
                        time.sleep(1)
                        continue
                    
                    for event in events:
                        event_id = event.GetEventID()
                        timestamp = event.GetEventRecord().TimeGenerated
                        computer = event.GetComputerName()
                        
                        source_name = event.GetSourceName()
                        event_type = event.GetEventType()
                        message = event.GetStringInserts()
                        
                        raw_event = {
                            "event_id": event_id,
                            "source": source_name,
                            "type": event_type,
                            "message": message,
                        }
                        
                        yield {
                            "campaign_id": "WINDOWS-EVENTLOG",
                            "event_id": str(uuid.uuid4()),
                            "timestamp": str(timestamp),
                            "host": computer,
                            "technique_id": None,
                            "source": "windows_eventlog",
                            "_raw": raw_event,
                        }
                        
                        record_id = event_id - 1
                    
                    retries = 0  # Reset on successful read
                
                except Exception as e:
                    print(f"[Windows EventLog] Error reading: {e}")
                    time.sleep(1)
        
        except Exception as e:
            retries += 1
            print(f"[Windows EventLog] Error (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                time.sleep(2 ** retries)
            else:
                raise


# ==========================================
# HELPER FUNCTION
# ==========================================

def get_connector(connector_type: str, **kwargs) -> Generator:
    """
    Factory function to get connector by type.
    
    Args:
        connector_type: 'kafka', 'websocket', 'rest', 'splunk', 'elastic', 'syslog', 'windows_eventlog'
        **kwargs: Arguments for specific connector
    
    Returns:
        Generator yielding events
    
    Example:
        source = get_connector('kafka', topic='events', bootstrap_servers=['localhost:9092'])
    """
    connectors = {
        'kafka': kafka_event_stream,
        'websocket': websocket_event_stream,
        'rest': rest_poll_event_stream,
        'splunk': splunk_event_stream,
        'elastic': elastic_event_stream,
        'syslog': syslog_event_stream,
        'windows_eventlog': windows_eventlog_stream,
    }
    
    if connector_type not in connectors:
        raise ValueError(
            f"Unknown connector: {connector_type}. "
            f"Available: {', '.join(connectors.keys())}"
        )
    
    return connectors[connector_type](**kwargs)
