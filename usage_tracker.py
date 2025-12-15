"""
Usage tracking module for monitoring Whisper API audio processing minutes and costs.

This module provides the UsageTracker class to track API usage, calculate costs,
and manage persistent storage of usage metrics with thread-safe operations.
"""

import json
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Thread-safe usage tracker for Whisper API transcription metrics.
    
    Tracks:
    - Total minutes processed
    - Successful vs failed transcription attempts
    - Daily and weekly aggregates
    - Estimated costs at $0.006 per minute
    
    Storage: JSON file in application directory (usage_data.json)
    Thread Safety: Uses threading.Lock for concurrent access
    """
    
    # Default cost per minute in USD
    COST_PER_MINUTE = 0.006
    
    # Default storage location
    DEFAULT_STORAGE_PATH = Path.home() / ".sokhan_negar" / "usage_data.json"
    
    def __init__(self, storage_path=None):
        """
        Initialize UsageTracker with thread-safe storage.
        
        Args:
            storage_path: Path to JSON storage file. Defaults to ~/.sokhan_negar/usage_data.json
        """
        self.storage_path = Path(storage_path) if storage_path else self.DEFAULT_STORAGE_PATH
        self._lock = threading.Lock()
        self._ensure_storage_directory()
        self._initialize_storage()
    
    def _ensure_storage_directory(self):
        """Create storage directory if it doesn't exist."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def _initialize_storage(self):
        """Initialize JSON storage file with default structure if it doesn't exist."""
        if not self.storage_path.exists():
            default_data = {
                "total_minutes": 0.0,
                "successful_minutes": 0.0,
                "failed_attempts": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "daily_aggregate": {},
                "weekly_aggregate": {}
            }
            self._write_data(default_data)
    
    def _read_data(self):
        """
        Read usage data from JSON file with error handling.
        
        Returns:
            dict: Usage data, or empty structure if file is corrupted
            
        Raises during read:
            - Logs warnings for corrupted files
            - Returns default structure as fallback
        """
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            # Validate data structure
            self._validate_data_structure(data)
            return data
        
        except FileNotFoundError:
            logger.warning(f"Usage data file not found at {self.storage_path}, creating new file")
            default_data = {
                "total_minutes": 0.0,
                "successful_minutes": 0.0,
                "failed_attempts": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "daily_aggregate": {},
                "weekly_aggregate": {}
            }
            self._write_data(default_data)
            return default_data
        
        except json.JSONDecodeError:
            logger.error(f"Usage data file corrupted at {self.storage_path}, reinitializing")
            # Backup corrupted file
            self._backup_corrupted_file()
            default_data = {
                "total_minutes": 0.0,
                "successful_minutes": 0.0,
                "failed_attempts": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "daily_aggregate": {},
                "weekly_aggregate": {}
            }
            self._write_data(default_data)
            return default_data
        
        except Exception as e:
            logger.error(f"Unexpected error reading usage data: {e}")
            default_data = {
                "total_minutes": 0.0,
                "successful_minutes": 0.0,
                "failed_attempts": 0,
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "daily_aggregate": {},
                "weekly_aggregate": {}
            }
            return default_data
    
    def _write_data(self, data):
        """
        Write usage data to JSON file with error handling.
        
        Args:
            data: Dictionary to write
            
        Raises:
            - Logs errors for write failures
            - Attempts to handle disk space errors
        """
        try:
            # Create temporary file to ensure atomic write
            temp_path = str(self.storage_path) + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename (safer than direct overwrite)
            os.replace(temp_path, self.storage_path)
        
        except OSError as e:
            if e.errno == 28:  # No space left on device
                logger.error(f"Disk space full, cannot write usage data: {e}")
            else:
                logger.error(f"OS error writing usage data: {e}")
        
        except Exception as e:
            logger.error(f"Failed to write usage data: {e}")
    
    def _validate_data_structure(self, data):
        """
        Validate and repair data structure if necessary.
        
        Args:
            data: Dictionary to validate
        """
        # Ensure required fields exist
        required_fields = {
            "total_minutes": 0.0,
            "successful_minutes": 0.0,
            "failed_attempts": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "daily_aggregate": {},
            "weekly_aggregate": {}
        }
        
        for field, default_value in required_fields.items():
            if field not in data:
                logger.warning(f"Missing field '{field}' in usage data, setting to default")
                data[field] = default_value
            
            # Type validation
            if field in ("total_minutes", "successful_minutes") and not isinstance(data[field], (int, float)):
                logger.warning(f"Field '{field}' has invalid type, resetting to 0.0")
                data[field] = 0.0
            
            if field == "failed_attempts" and not isinstance(data[field], int):
                logger.warning(f"Field '{field}' has invalid type, resetting to 0")
                data[field] = 0
            
            if field in ("daily_aggregate", "weekly_aggregate") and not isinstance(data[field], dict):
                logger.warning(f"Field '{field}' has invalid type, resetting to empty dict")
                data[field] = {}
    
    def _backup_corrupted_file(self):
        """Backup corrupted data file with timestamp."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.storage_path}.backup_{timestamp}"
            if self.storage_path.exists():
                self.storage_path.rename(backup_path)
                logger.info(f"Corrupted file backed up to: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup corrupted file: {e}")
    
    def _get_week_key(self, date=None):
        """
        Get week key in format YYYY-Www (ISO week format).
        
        Args:
            date: datetime object or None for current date
            
        Returns:
            str: Week key in format YYYY-Www
        """
        if date is None:
            date = datetime.now()
        year, week, _ = date.isocalendar()
        return f"{year}-W{week:02d}"
    
    def _get_day_key(self, date=None):
        """
        Get day key in format YYYY-MM-DD.
        
        Args:
            date: datetime object or None for current date
            
        Returns:
            str: Day key in format YYYY-MM-DD
        """
        if date is None:
            date = datetime.now()
        return date.strftime("%Y-%m-%d")
    
    def track_audio_duration(self, duration_seconds, success=True):
        """
        Track audio duration in minutes from API call.
        
        Args:
            duration_seconds: Duration of audio in seconds (typically 5 for each chunk)
            success: Whether transcription was successful (True) or failed (False)
            
        Returns:
            dict: Updated usage statistics
        """
        if duration_seconds <= 0:
            logger.warning(f"Invalid duration: {duration_seconds}s, skipping tracking")
            return self.get_usage_stats()
        
        with self._lock:
            try:
                data = self._read_data()
                duration_minutes = duration_seconds / 60.0
                
                # Update total minutes
                data["total_minutes"] = float(data.get("total_minutes", 0)) + duration_minutes
                
                # Track successful vs failed
                if success:
                    data["successful_minutes"] = float(data.get("successful_minutes", 0)) + duration_minutes
                else:
                    data["failed_attempts"] = int(data.get("failed_attempts", 0)) + 1
                
                # Update daily aggregate
                day_key = self._get_day_key()
                if "daily_aggregate" not in data:
                    data["daily_aggregate"] = {}
                data["daily_aggregate"][day_key] = float(data["daily_aggregate"].get(day_key, 0)) + duration_minutes
                
                # Update weekly aggregate
                week_key = self._get_week_key()
                if "weekly_aggregate" not in data:
                    data["weekly_aggregate"] = {}
                data["weekly_aggregate"][week_key] = float(data["weekly_aggregate"].get(week_key, 0)) + duration_minutes
                
                # Update timestamp
                data["last_updated"] = datetime.utcnow().isoformat()
                
                # Write updated data
                self._write_data(data)
                
                logger.info(f"Tracked {duration_minutes:.4f} minutes (success={success}). Total: {data['total_minutes']:.2f} minutes")
                return self._format_stats(data)
            
            except Exception as e:
                logger.error(f"Error tracking audio duration: {e}")
                return self.get_usage_stats()
    
    def get_usage_stats(self):
        """
        Get current usage statistics.
        
        Returns:
            dict: Current usage stats with cost calculation
        """
        with self._lock:
            try:
                data = self._read_data()
                return self._format_stats(data)
            except Exception as e:
                logger.error(f"Error getting usage stats: {e}")
                return {
                    "total_minutes": 0.0,
                    "estimated_cost": "$0.00",
                    "successful_minutes": 0.0,
                    "failed_attempts": 0,
                    "daily_minutes": 0.0,
                    "weekly_minutes": 0.0,
                    "error": str(e)
                }
    
    def _format_stats(self, data):
        """
        Format statistics for display with cost calculation.
        
        Args:
            data: Raw usage data dictionary
            
        Returns:
            dict: Formatted statistics
        """
        total_minutes = float(data.get("total_minutes", 0))
        successful_minutes = float(data.get("successful_minutes", 0))
        failed_attempts = int(data.get("failed_attempts", 0))
        
        # Calculate estimated cost
        estimated_cost = total_minutes * self.COST_PER_MINUTE
        cost_str = f"${estimated_cost:.2f}"
        
        # Get current day/week aggregates
        day_key = self._get_day_key()
        week_key = self._get_week_key()
        daily_minutes = float(data.get("daily_aggregate", {}).get(day_key, 0))
        weekly_minutes = float(data.get("weekly_aggregate", {}).get(week_key, 0))
        
        return {
            "total_minutes": round(total_minutes, 2),
            "estimated_cost": cost_str,
            "successful_minutes": round(successful_minutes, 2),
            "failed_attempts": failed_attempts,
            "daily_minutes": round(daily_minutes, 2),
            "weekly_minutes": round(weekly_minutes, 2),
            "created_at": data.get("created_at"),
            "last_updated": data.get("last_updated")
        }
    
    def reset_usage(self, period="all"):
        """
        Reset usage metrics for specified period.
        
        Args:
            period: "daily", "weekly", "monthly", or "all" (default: "all")
            
        Returns:
            dict: Updated usage statistics after reset
        """
        with self._lock:
            try:
                data = self._read_data()
                
                if period == "daily":
                    day_key = self._get_day_key()
                    if "daily_aggregate" in data and day_key in data["daily_aggregate"]:
                        daily_minutes = data["daily_aggregate"][day_key]
                        data["total_minutes"] = float(data.get("total_minutes", 0)) - daily_minutes
                        data["daily_aggregate"][day_key] = 0.0
                        logger.info(f"Reset daily usage for {day_key}")
                
                elif period == "weekly":
                    week_key = self._get_week_key()
                    if "weekly_aggregate" in data and week_key in data["weekly_aggregate"]:
                        weekly_minutes = data["weekly_aggregate"][week_key]
                        data["total_minutes"] = float(data.get("total_minutes", 0)) - weekly_minutes
                        data["weekly_aggregate"][week_key] = 0.0
                        logger.info(f"Reset weekly usage for {week_key}")
                
                elif period == "all":
                    logger.info(f"Reset all usage data. Previous total: {data.get('total_minutes', 0):.2f} minutes")
                    data["total_minutes"] = 0.0
                    data["successful_minutes"] = 0.0
                    data["failed_attempts"] = 0
                    data["daily_aggregate"] = {}
                    data["weekly_aggregate"] = {}
                
                else:
                    logger.warning(f"Unknown reset period: {period}")
                    return self.get_usage_stats()
                
                data["last_updated"] = datetime.utcnow().isoformat()
                self._write_data(data)
                return self._format_stats(data)
            
            except Exception as e:
                logger.error(f"Error resetting usage: {e}")
                return self.get_usage_stats()
    
    def get_cost_warning(self, threshold_cost=1.0):
        """
        Check if estimated cost exceeds threshold.
        
        Args:
            threshold_cost: Cost threshold in USD (default: $1.00)
            
        Returns:
            tuple: (is_over_threshold, current_cost, threshold_cost)
        """
        try:
            stats = self.get_usage_stats()
            cost_str = stats["estimated_cost"]
            current_cost = float(cost_str.replace("$", ""))
            return (current_cost > threshold_cost, current_cost, threshold_cost)
        except Exception as e:
            logger.error(f"Error checking cost warning: {e}")
            return (False, 0.0, threshold_cost)


# Global instance for module-level access
_tracker_instance = None


def get_tracker(storage_path=None):
    """
    Get or create global UsageTracker instance (singleton pattern).
    
    Args:
        storage_path: Custom storage path (used only on first call)
        
    Returns:
        UsageTracker: Global tracker instance
    """
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = UsageTracker(storage_path)
    return _tracker_instance
