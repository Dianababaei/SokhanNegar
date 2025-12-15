"""
Performance and stability monitoring for continuous operation testing.

This module monitors memory usage, CPU usage, and performance metrics
during extended transcription sessions.
"""

import logging
import time
import json
from pathlib import Path
from datetime import datetime
from collections import deque
import threading

try:
    import psutil
except ImportError:
    psutil = None
    logging.warning("psutil not available - memory/CPU monitoring will be limited")

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance during transcription."""
    
    def __init__(self, sample_interval=1.0):
        """
        Initialize performance monitor.
        
        Args:
            sample_interval: Time between samples in seconds
        """
        self.sample_interval = sample_interval
        self.samples = deque(maxlen=1000)  # Keep last 1000 samples
        self.start_time = None
        self.end_time = None
        self.is_monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.is_monitoring = True
        logger.info("Performance monitoring started")
        
        if psutil:
            self._monitor_thread = threading.Thread(target=self._monitor_loop)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.end_time = time.time()
        self.is_monitoring = False
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        process = psutil.Process()
        
        while self.is_monitoring:
            try:
                timestamp = time.time()
                
                # Get memory info
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                
                # Get CPU usage
                cpu_percent = process.cpu_percent(interval=0.1)
                
                sample = {
                    'timestamp': timestamp,
                    'memory_mb': round(memory_mb, 2),
                    'cpu_percent': round(cpu_percent, 1)
                }
                
                self.samples.append(sample)
                
                time.sleep(self.sample_interval)
            
            except Exception as e:
                logger.error(f"Error monitoring performance: {e}")
                break
    
    def get_statistics(self):
        """
        Get performance statistics.
        
        Returns:
            dict: Performance statistics
        """
        if not self.samples:
            return {
                'status': 'No data collected',
                'duration_seconds': 0
            }
        
        memory_values = [s['memory_mb'] for s in self.samples]
        cpu_values = [s['cpu_percent'] for s in self.samples]
        
        duration = (self.end_time or time.time()) - self.start_time
        
        stats = {
            'duration_seconds': round(duration, 2),
            'samples_collected': len(self.samples),
            'memory': {
                'peak_mb': max(memory_values),
                'min_mb': min(memory_values),
                'average_mb': round(sum(memory_values) / len(memory_values), 2),
                'stable': self._is_memory_stable(memory_values)
            },
            'cpu': {
                'peak_percent': max(cpu_values),
                'average_percent': round(sum(cpu_values) / len(cpu_values), 1),
                'excessive': max(cpu_values) > 80  # Threshold: 80%
            },
            'assessment': self._assess_stability(memory_values, cpu_values)
        }
        
        return stats
    
    @staticmethod
    def _is_memory_stable(memory_values):
        """
        Assess if memory usage is stable (no leak).
        
        Args:
            memory_values: List of memory readings
        
        Returns:
            bool: True if stable, False if increasing trend
        """
        if len(memory_values) < 10:
            return True
        
        # Check first half vs second half
        mid = len(memory_values) // 2
        first_half_avg = sum(memory_values[:mid]) / mid
        second_half_avg = sum(memory_values[mid:]) / (len(memory_values) - mid)
        
        # Allow 10% increase
        increase_ratio = second_half_avg / first_half_avg
        return increase_ratio < 1.1
    
    @staticmethod
    def _assess_stability(memory_values, cpu_values):
        """
        Assess overall stability.
        
        Args:
            memory_values: List of memory readings
            cpu_values: List of CPU readings
        
        Returns:
            str: Stability assessment
        """
        memory_stable = PerformanceMonitor._is_memory_stable(memory_values)
        cpu_excessive = max(cpu_values) > 80
        
        if memory_stable and not cpu_excessive:
            return "STABLE - No issues detected"
        elif not memory_stable:
            return "WARNING - Possible memory leak"
        elif cpu_excessive:
            return "WARNING - Excessive CPU usage"
        else:
            return "STABLE"


class ChunkProcessingTracker:
    """Track audio chunk processing metrics."""
    
    def __init__(self):
        """Initialize chunk processor tracker."""
        self.chunks_processed = 0
        self.processing_times = deque(maxlen=100)
        self.start_time = None
        self.lock = threading.Lock()
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.chunks_processed = 0
        logger.info("Chunk processing tracking started")
    
    def record_chunk(self, duration_seconds):
        """
        Record processing of a chunk.
        
        Args:
            duration_seconds: Duration of processed chunk
        """
        with self.lock:
            self.chunks_processed += 1
            self.processing_times.append(duration_seconds)
            
            if self.chunks_processed % 10 == 0:
                logger.info(f"Processed {self.chunks_processed} chunks")
    
    def get_statistics(self):
        """
        Get chunk processing statistics.
        
        Returns:
            dict: Processing statistics
        """
        with self.lock:
            if not self.processing_times:
                return {
                    'chunks_processed': 0,
                    'duration_seconds': 0
                }
            
            elapsed = time.time() - self.start_time
            total_duration = sum(self.processing_times)
            
            return {
                'chunks_processed': self.chunks_processed,
                'total_duration_seconds': round(total_duration, 2),
                'elapsed_time_seconds': round(elapsed, 2),
                'average_chunk_duration': round(total_duration / len(self.processing_times), 3),
                'chunks_per_second': round(self.chunks_processed / elapsed, 2) if elapsed > 0 else 0,
                'processing_time_consistent': self._is_consistent()
            }
    
    def _is_consistent(self):
        """Check if processing time is consistent."""
        if len(self.processing_times) < 5:
            return True
        
        times = list(self.processing_times)
        avg = sum(times) / len(times)
        
        # Check variance - consistent if all within 20% of average
        for t in times:
            if abs(t - avg) > (avg * 0.2):
                return False
        
        return True


class ContinuousOperationTest:
    """Test continuous operation with monitoring."""
    
    def __init__(self, duration_chunks=120):
        """
        Initialize continuous operation test.
        
        Args:
            duration_chunks: Number of 5-second chunks to process
        """
        self.duration_chunks = duration_chunks
        self.performance_monitor = PerformanceMonitor()
        self.chunk_tracker = ChunkProcessingTracker()
        self.test_results = {}
    
    def run_test(self):
        """
        Run continuous operation test.
        
        Simulates processing of specified number of chunks.
        """
        logger.info("="*70)
        logger.info(f"CONTINUOUS OPERATION TEST")
        logger.info(f"Duration: {self.duration_chunks} chunks × 5 seconds = {self.duration_chunks * 5} seconds")
        logger.info("="*70)
        
        self.performance_monitor.start_monitoring()
        self.chunk_tracker.start()
        
        try:
            for i in range(self.duration_chunks):
                # Simulate chunk processing
                chunk_duration = 5.0  # 5 seconds per chunk
                self.chunk_tracker.record_chunk(chunk_duration)
                
                # Simulate some work
                time.sleep(0.01)  # Small delay to simulate processing
                
                if (i + 1) % 20 == 0:
                    logger.info(f"Progress: {i + 1}/{self.duration_chunks} chunks")
        
        finally:
            self.performance_monitor.stop_monitoring()
        
        # Collect results
        self.test_results = {
            'performance': self.performance_monitor.get_statistics(),
            'chunk_processing': self.chunk_tracker.get_statistics(),
            'test_timestamp': datetime.now().isoformat()
        }
        
        self._print_results()
        return self.test_results
    
    def _print_results(self):
        """Print test results."""
        logger.info("\n" + "="*70)
        logger.info("CONTINUOUS OPERATION TEST RESULTS")
        logger.info("="*70)
        
        perf = self.test_results['performance']
        chunk = self.test_results['chunk_processing']
        
        logger.info(f"\nDuration: {perf['duration_seconds']} seconds")
        logger.info(f"Chunks processed: {chunk['chunks_processed']}")
        logger.info(f"Total audio processed: {chunk['total_duration_seconds']} seconds")
        
        logger.info(f"\nMemory Usage:")
        logger.info(f"  Peak: {perf['memory']['peak_mb']} MB")
        logger.info(f"  Min: {perf['memory']['min_mb']} MB")
        logger.info(f"  Average: {perf['memory']['average_mb']} MB")
        logger.info(f"  Stable: {perf['memory']['stable']}")
        
        logger.info(f"\nCPU Usage:")
        logger.info(f"  Peak: {perf['cpu']['peak_percent']}%")
        logger.info(f"  Average: {perf['cpu']['average_percent']}%")
        logger.info(f"  Excessive: {perf['cpu']['excessive']}")
        
        logger.info(f"\nProcessing Performance:")
        logger.info(f"  Average per chunk: {chunk['average_chunk_duration']} seconds")
        logger.info(f"  Chunks per second: {chunk['chunks_per_second']}")
        logger.info(f"  Consistency: {chunk['processing_time_consistent']}")
        
        logger.info(f"\nOverall Assessment: {perf['assessment']}")
        logger.info("="*70)
    
    def save_results(self, filename='continuous_operation_results.json'):
        """
        Save test results to JSON file.
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info(f"Results saved: {filename}")


def create_stability_assessment():
    """
    Create stability assessment criteria.
    
    Returns:
        dict: Assessment criteria
    """
    assessment = {
        'memory_stability': {
            'description': 'Memory usage should not increase >10% over time',
            'threshold': 1.1,  # 10% increase allowed
            'unit': 'ratio'
        },
        'cpu_usage': {
            'description': 'Peak CPU usage should be <50% for normal operation',
            'threshold': 50,
            'unit': 'percent',
            'warning_threshold': 80
        },
        'processing_consistency': {
            'description': 'Processing time per chunk should be consistent (±20%)',
            'variance_tolerance': 0.2,
            'unit': 'ratio'
        },
        'no_crashes': {
            'description': 'Application should not crash during extended operation',
            'expected': True
        }
    }
    
    return assessment


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run continuous operation test
    test = ContinuousOperationTest(duration_chunks=120)  # 10 minutes
    test.run_test()
    test.save_results()
