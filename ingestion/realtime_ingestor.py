"""
Real-Time Event Ingestion Engine

Provides thread-safe, configurable streaming and batch processing of telemetry events.
Designed for extensibility to Kafka, WebSocket, REST, and SIEM integration.
"""

import threading
import queue
import time
import uuid
from datetime import datetime, timezone
from typing import Callable, Generator, List, Dict, Any, Optional
from collections import deque


class RealTimeIngestor:
    """
    Thread-safe real-time event ingestion engine.
    
    Capabilities:
    - Continuous event stream ingestion
    - Configurable batch processing (by event count or time window)
    - Internal thread-safe event queue
    - Sliding window processing
    - Callback hooks for analytics pipeline integration
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        time_window_seconds: float = 5.0,
        event_source: Optional[Generator] = None,
        max_queue_size: int = 1000,
    ):
        """
        Initialize RealTimeIngestor.
        
        Args:
            batch_size: Number of events to accumulate before triggering batch processing
            time_window_seconds: Time window (seconds) for sliding window aggregation
            event_source: Generator that yields events (pluggable source)
            max_queue_size: Maximum size of internal event queue
        """
        self.batch_size = batch_size
        self.time_window_seconds = time_window_seconds
        self.event_source = event_source
        self.max_queue_size = max_queue_size
        
        # Thread-safe components
        self._event_queue = queue.Queue(maxsize=max_queue_size)
        self._batch_buffer = deque(maxlen=batch_size)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Ingestion state
        self._event_count = 0
        self._processed_batches = 0
        self._last_batch_time = time.time()
        
        # Callback hooks for analytics pipeline
        self._on_batch_ready: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        self._on_event_ingested: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Worker threads
        self._ingestor_thread: Optional[threading.Thread] = None
        self._processor_thread: Optional[threading.Thread] = None
    
    def set_event_source(self, event_source: Generator) -> None:
        """
        Set or update the event source generator.
        
        Args:
            event_source: Generator that yields events
        """
        with self._lock:
            self.event_source = event_source
    
    def register_batch_callback(self, callback: Callable[[List[Dict[str, Any]]], None]) -> None:
        """
        Register callback to be invoked when a batch is ready.
        
        Args:
            callback: Function that accepts a list of events
        """
        with self._lock:
            self._on_batch_ready = callback
    
    def register_event_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Register callback to be invoked when each event is ingested.
        
        Args:
            callback: Function that accepts a single event
        """
        with self._lock:
            self._on_event_ingested = callback
    
    def _ingestor_worker(self) -> None:
        """
        Worker thread: continuously pulls events from source and queues them.
        """
        if not self.event_source:
            print("[RealTimeIngestor] No event source configured. Ingestor idle.")
            return
        
        try:
            for event in self.event_source:
                if self._stop_event.is_set():
                    break
                
                try:
                    # Non-blocking put with timeout to respect stop signal
                    self._event_queue.put(event, timeout=1.0)
                    
                    with self._lock:
                        self._event_count += 1
                    
                    # Fire event-level callback
                    if self._on_event_ingested:
                        self._on_event_ingested(event)
                
                except queue.Full:
                    print("[RealTimeIngestor] Event queue full, dropping event")
        
        except Exception as e:
            print(f"[RealTimeIngestor] Ingestor worker error: {e}")
        finally:
            print("[RealTimeIngestor] Ingestor worker stopped")
    
    def _processor_worker(self) -> None:
        """
        Worker thread: accumulates events and triggers batch processing based on 
        batch_size or time_window_seconds.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Non-blocking attempt to dequeue with timeout
                    event = self._event_queue.get(timeout=0.5)
                    
                    with self._lock:
                        self._batch_buffer.append(event)
                        buffer_size = len(self._batch_buffer)
                        elapsed = time.time() - self._last_batch_time
                    
                    # Check if batch is ready (by size or time)
                    if (buffer_size >= self.batch_size or 
                        elapsed >= self.time_window_seconds):
                        self._process_batch()
                
                except queue.Empty:
                    # Check if time-based window elapsed
                    with self._lock:
                        elapsed = time.time() - self._last_batch_time
                        buffer_size = len(self._batch_buffer)
                    
                    if buffer_size > 0 and elapsed >= self.time_window_seconds:
                        self._process_batch()
        
        except Exception as e:
            print(f"[RealTimeIngestor] Processor worker error: {e}")
        finally:
            # Process any remaining events in buffer
            with self._lock:
                if len(self._batch_buffer) > 0:
                    self._process_batch()
            print("[RealTimeIngestor] Processor worker stopped")
    
    def _process_batch(self) -> None:
        """
        Internal: Process accumulated batch and invoke batch callback.
        Must be called under lock.
        """
        if len(self._batch_buffer) == 0:
            return
        
        batch = list(self._batch_buffer)
        self._batch_buffer.clear()
        self._last_batch_time = time.time()
        self._processed_batches += 1
        
        # Release lock before callback to avoid deadlock
        on_batch_callback = self._on_batch_ready
        
        if on_batch_callback:
            try:
                on_batch_callback(batch)
            except Exception as e:
                print(f"[RealTimeIngestor] Batch callback error: {e}")
    
    def start(self) -> None:
        """
        Start ingestor and processor worker threads.
        """
        if self._ingestor_thread and self._ingestor_thread.is_alive():
            print("[RealTimeIngestor] Already running")
            return
        
        self._stop_event.clear()
        
        self._ingestor_thread = threading.Thread(
            target=self._ingestor_worker,
            name="RealTimeIngestor-Ingestor",
            daemon=True
        )
        
        self._processor_thread = threading.Thread(
            target=self._processor_worker,
            name="RealTimeIngestor-Processor",
            daemon=True
        )
        
        self._ingestor_thread.start()
        self._processor_thread.start()
        print("[RealTimeIngestor] Started (ingestor and processor threads)")
    
    def stop(self) -> None:
        """
        Gracefully stop ingestor and processor threads.
        """
        print("[RealTimeIngestor] Stopping...")
        self._stop_event.set()
        
        if self._ingestor_thread:
            self._ingestor_thread.join(timeout=5.0)
        
        if self._processor_thread:
            self._processor_thread.join(timeout=5.0)
        
        print("[RealTimeIngestor] Stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get ingestion statistics.
        
        Returns:
            Dictionary with event count, processed batches, queue size, etc.
        """
        with self._lock:
            return {
                "total_events_ingested": self._event_count,
                "total_batches_processed": self._processed_batches,
                "current_buffer_size": len(self._batch_buffer),
                "queue_size": self._event_queue.qsize(),
                "batch_size_config": self.batch_size,
                "time_window_config": self.time_window_seconds,
            }


def create_simulated_event_stream(
    campaign_id: str,
    num_events: int = 50,
    techniques_pool: Optional[List[str]] = None,
    delay_seconds: float = 0.1
) -> Generator:
    """
    Generate a simulated stream of telemetry events (for testing/demo).
    
    Args:
        campaign_id: Campaign identifier
        num_events: Number of events to generate
        techniques_pool: List of technique IDs to randomly select from
        delay_seconds: Delay between generated events (simulates streaming)
    
    Yields:
        Event dictionaries
    """
    if not techniques_pool:
        techniques_pool = ["T1059", "T1547", "T1003", "T1021", "T1041"]
    
    import random
    
    for i in range(num_events):
        event = {
            "campaign_id": campaign_id,
            "event_id": str(uuid.uuid4()),
            "timestamp": str(datetime.now(timezone.utc)),
            "host": f"HOST-{random.randint(1, 5)}",
            "technique_id": random.choice(techniques_pool),
            "source": "simulated_stream"
        }
        
        time.sleep(delay_seconds)
        yield event
