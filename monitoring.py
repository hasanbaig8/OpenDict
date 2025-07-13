"""
OpenDict Monitoring and Health Check System
Comprehensive monitoring, health checks, and performance metrics
"""

import json
import os
import socket
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil

from config import get_config
from error_handling import ErrorCode, OpenDictError
from logging_config import get_logger


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    name: str
    status: HealthStatus
    message: str
    timestamp: float
    duration_ms: float
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }


@dataclass
class Metric:
    """Performance metric."""

    name: str
    type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }


class HealthChecker:
    """Health check manager."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.config = get_config()
        self.checks = {}
        self.last_results = {}
        self.check_history = []
        self.max_history = 100

    def register_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Register a health check."""
        self.checks[name] = check_func
        self.logger.info(f"Health check registered: {name}")

    def unregister_check(self, name: str):
        """Unregister a health check."""
        if name in self.checks:
            del self.checks[name]
            self.logger.info(f"Health check unregistered: {name}")

    def run_check(self, name: str) -> HealthCheckResult:
        """Run a specific health check."""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNKNOWN,
                message="Check not found",
                timestamp=time.time(),
                duration_ms=0,
            )

        start_time = time.time()
        try:
            result = self.checks[name]()
            result.timestamp = start_time
            result.duration_ms = (time.time() - start_time) * 1000

            # Store result
            self.last_results[name] = result
            self.check_history.append(result)

            # Limit history size
            if len(self.check_history) > self.max_history:
                self.check_history = self.check_history[-self.max_history :]

            return result

        except Exception as e:
            self.logger.exception(f"Health check failed: {name}")
            result = HealthCheckResult(
                name=name,
                status=HealthStatus.CRITICAL,
                message=f"Check failed: {str(e)}",
                timestamp=start_time,
                duration_ms=(time.time() - start_time) * 1000,
                details={"exception": str(e)},
            )
            self.last_results[name] = result
            return result

    def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results

    def get_overall_health(self) -> HealthCheckResult:
        """Get overall system health."""
        results = self.run_all_checks()

        if not results:
            return HealthCheckResult(
                name="overall",
                status=HealthStatus.UNKNOWN,
                message="No health checks registered",
                timestamp=time.time(),
                duration_ms=0,
            )

        # Determine overall status
        statuses = [result.status for result in results.values()]

        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
            message = "System has critical issues"
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
            message = "System has warnings"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "System is healthy"

        return HealthCheckResult(
            name="overall",
            status=overall_status,
            message=message,
            timestamp=time.time(),
            duration_ms=0,
            details={
                "checks": {name: result.to_dict() for name, result in results.items()},
                "healthy_checks": len(
                    [s for s in statuses if s == HealthStatus.HEALTHY]
                ),
                "warning_checks": len(
                    [s for s in statuses if s == HealthStatus.WARNING]
                ),
                "critical_checks": len(
                    [s for s in statuses if s == HealthStatus.CRITICAL]
                ),
            },
        )

    def get_check_history(self, name: Optional[str] = None) -> List[HealthCheckResult]:
        """Get health check history."""
        if name:
            return [result for result in self.check_history if result.name == name]
        return self.check_history.copy()


class MetricsCollector:
    """Metrics collection and aggregation."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.metrics = []
        self.aggregated_metrics = {}
        self.max_metrics = 1000
        self.lock = threading.Lock()

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Dict[str, str] = None,
    ):
        """Record a metric."""
        with self.lock:
            metric = Metric(
                name=name,
                type=metric_type,
                value=value,
                timestamp=time.time(),
                tags=tags or {},
            )

            self.metrics.append(metric)

            # Limit metrics size
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics :]

            # Update aggregated metrics
            self._update_aggregated_metrics(metric)

    def _update_aggregated_metrics(self, metric: Metric):
        """Update aggregated metrics."""
        key = f"{metric.name}:{metric.type.value}"

        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                "name": metric.name,
                "type": metric.type.value,
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "avg": 0.0,
                "last_value": 0.0,
                "last_timestamp": 0.0,
            }

        agg = self.aggregated_metrics[key]
        agg["count"] += 1
        agg["sum"] += metric.value
        agg["min"] = min(agg["min"], metric.value)
        agg["max"] = max(agg["max"], metric.value)
        agg["avg"] = agg["sum"] / agg["count"]
        agg["last_value"] = metric.value
        agg["last_timestamp"] = metric.timestamp

    def get_metrics(self, name: Optional[str] = None, limit: int = 100) -> List[Metric]:
        """Get metrics."""
        with self.lock:
            if name:
                filtered = [m for m in self.metrics if m.name == name]
                return filtered[-limit:]
            return self.metrics[-limit:]

    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics."""
        with self.lock:
            return self.aggregated_metrics.copy()

    def increment_counter(
        self, name: str, value: float = 1.0, tags: Dict[str, str] = None
    ):
        """Increment a counter metric."""
        self.record_metric(name, value, MetricType.COUNTER, tags)

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric."""
        self.record_metric(name, value, MetricType.GAUGE, tags)

    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record a timer metric."""
        self.record_metric(name, duration_ms, MetricType.TIMER, tags)


class SystemMonitor:
    """System resource monitoring."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.metrics_collector = MetricsCollector(logger)
        self.monitoring_thread = None
        self.monitoring_active = False
        self.monitoring_interval = 5  # seconds

    def start_monitoring(self, interval: int = 5):
        """Start system monitoring."""
        self.monitoring_interval = interval
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info(f"System monitoring started with {interval}s interval")

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        self.logger.info("System monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.exception("Error in monitoring loop")
                time.sleep(self.monitoring_interval)

    def _collect_system_metrics(self):
        """Collect system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics_collector.set_gauge("system.cpu.usage_percent", cpu_percent)

        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics_collector.set_gauge("system.memory.usage_percent", memory.percent)
        self.metrics_collector.set_gauge("system.memory.used_bytes", memory.used)
        self.metrics_collector.set_gauge(
            "system.memory.available_bytes", memory.available
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        self.metrics_collector.set_gauge("system.disk.usage_percent", disk.percent)
        self.metrics_collector.set_gauge("system.disk.used_bytes", disk.used)
        self.metrics_collector.set_gauge("system.disk.free_bytes", disk.free)

        # Network metrics
        net_io = psutil.net_io_counters()
        self.metrics_collector.set_gauge("system.network.bytes_sent", net_io.bytes_sent)
        self.metrics_collector.set_gauge("system.network.bytes_recv", net_io.bytes_recv)

        # Process metrics
        process = psutil.Process()
        self.metrics_collector.set_gauge(
            "process.cpu.usage_percent", process.cpu_percent()
        )
        self.metrics_collector.set_gauge(
            "process.memory.rss_bytes", process.memory_info().rss
        )
        self.metrics_collector.set_gauge(
            "process.memory.vms_bytes", process.memory_info().vms
        )

        # File descriptor count
        try:
            self.metrics_collector.set_gauge(
                "process.file_descriptors", process.num_fds()
            )
        except AttributeError:
            pass  # Not available on all platforms

    def get_system_health(self) -> HealthCheckResult:
        """Get system health based on metrics."""
        try:
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Determine health status
            issues = []
            status = HealthStatus.HEALTHY

            # Check CPU usage
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif cpu_percent > 70:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING

            # Check memory usage
            if memory.percent > 95:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif memory.percent > 80:
                issues.append(f"Elevated memory usage: {memory.percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING

            # Check disk usage
            if disk.percent > 95:
                issues.append(f"High disk usage: {disk.percent:.1f}%")
                status = HealthStatus.CRITICAL
            elif disk.percent > 85:
                issues.append(f"Elevated disk usage: {disk.percent:.1f}%")
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.WARNING

            message = "System resources are healthy"
            if issues:
                message = "; ".join(issues)

            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                timestamp=time.time(),
                duration_ms=0,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_free_gb": disk.free / (1024**3),
                },
            )

        except Exception as e:
            return HealthCheckResult(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"Failed to check system resources: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"exception": str(e)},
            )


class ApplicationMonitor:
    """Application-specific monitoring."""

    def __init__(self, logger=None):
        self.logger = logger or get_logger()
        self.config = get_config()
        self.health_checker = HealthChecker(logger)
        self.metrics_collector = MetricsCollector(logger)
        self.system_monitor = SystemMonitor(logger)

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self):
        """Register default health checks."""
        self.health_checker.register_check(
            "system_resources", self.system_monitor.get_system_health
        )
        self.health_checker.register_check(
            "server_connectivity", self._check_server_connectivity
        )
        self.health_checker.register_check(
            "model_availability", self._check_model_availability
        )
        self.health_checker.register_check("disk_space", self._check_disk_space)
        self.health_checker.register_check("permissions", self._check_permissions)

    def _check_server_connectivity(self) -> HealthCheckResult:
        """Check if server port is accessible."""
        try:
            host = self.config.server.host
            port = self.config.server.port

            # Try to connect to server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return HealthCheckResult(
                    name="server_connectivity",
                    status=HealthStatus.HEALTHY,
                    message=f"Server accessible at {host}:{port}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"host": host, "port": port},
                )
            else:
                return HealthCheckResult(
                    name="server_connectivity",
                    status=HealthStatus.CRITICAL,
                    message=f"Server not accessible at {host}:{port}",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"host": host, "port": port, "error_code": result},
                )

        except Exception as e:
            return HealthCheckResult(
                name="server_connectivity",
                status=HealthStatus.CRITICAL,
                message=f"Server connectivity check failed: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"exception": str(e)},
            )

    def _check_model_availability(self) -> HealthCheckResult:
        """Check if transcription model is available."""
        try:
            cache_dir = os.path.expanduser(self.config.transcription.cache_dir)
            model_cache_path = os.path.join(cache_dir, "parakeet_model.pkl")

            if os.path.exists(model_cache_path):
                # Check if cache is readable
                try:
                    with open(model_cache_path, "rb") as f:
                        f.read(1024)  # Read first KB to test

                    cache_size = os.path.getsize(model_cache_path)
                    return HealthCheckResult(
                        name="model_availability",
                        status=HealthStatus.HEALTHY,
                        message="Model cache is available and readable",
                        timestamp=time.time(),
                        duration_ms=0,
                        details={
                            "cache_path": model_cache_path,
                            "cache_size_mb": cache_size / (1024**2),
                        },
                    )
                except Exception as e:
                    return HealthCheckResult(
                        name="model_availability",
                        status=HealthStatus.CRITICAL,
                        message=f"Model cache exists but not readable: {str(e)}",
                        timestamp=time.time(),
                        duration_ms=0,
                        details={"cache_path": model_cache_path, "error": str(e)},
                    )
            else:
                return HealthCheckResult(
                    name="model_availability",
                    status=HealthStatus.WARNING,
                    message="Model cache not found, will download on first use",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"cache_path": model_cache_path},
                )

        except Exception as e:
            return HealthCheckResult(
                name="model_availability",
                status=HealthStatus.CRITICAL,
                message=f"Model availability check failed: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"exception": str(e)},
            )

    def _check_disk_space(self) -> HealthCheckResult:
        """Check available disk space."""
        try:
            # Check main disk
            disk_usage = psutil.disk_usage("/")
            free_gb = disk_usage.free / (1024**3)

            # Check cache directory
            cache_dir = os.path.expanduser(self.config.transcription.cache_dir)
            cache_disk_usage = psutil.disk_usage(cache_dir)
            cache_free_gb = cache_disk_usage.free / (1024**3)

            # Determine status
            min_free_gb = 1.0  # Minimum 1GB free space
            if free_gb < min_free_gb or cache_free_gb < min_free_gb:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.CRITICAL,
                    message=f"Low disk space: {free_gb:.1f}GB free",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "main_disk_free_gb": free_gb,
                        "cache_disk_free_gb": cache_free_gb,
                        "min_required_gb": min_free_gb,
                    },
                )
            elif free_gb < 5.0:  # Warning at 5GB
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.WARNING,
                    message=f"Disk space getting low: {free_gb:.1f}GB free",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "main_disk_free_gb": free_gb,
                        "cache_disk_free_gb": cache_free_gb,
                    },
                )
            else:
                return HealthCheckResult(
                    name="disk_space",
                    status=HealthStatus.HEALTHY,
                    message=f"Disk space is adequate: {free_gb:.1f}GB free",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "main_disk_free_gb": free_gb,
                        "cache_disk_free_gb": cache_free_gb,
                    },
                )

        except Exception as e:
            return HealthCheckResult(
                name="disk_space",
                status=HealthStatus.CRITICAL,
                message=f"Disk space check failed: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"exception": str(e)},
            )

    def _check_permissions(self) -> HealthCheckResult:
        """Check file permissions."""
        try:
            issues = []

            # Check cache directory permissions
            cache_dir = os.path.expanduser(self.config.transcription.cache_dir)
            if not os.path.exists(cache_dir):
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create cache directory: {str(e)}")

            if os.path.exists(cache_dir):
                if not os.access(cache_dir, os.W_OK):
                    issues.append(f"Cache directory not writable: {cache_dir}")
                if not os.access(cache_dir, os.R_OK):
                    issues.append(f"Cache directory not readable: {cache_dir}")

            # Check log directory permissions
            if self.config.logging.file:
                log_dir = os.path.dirname(self.config.logging.file)
                if not os.path.exists(log_dir):
                    try:
                        os.makedirs(log_dir, exist_ok=True)
                    except Exception as e:
                        issues.append(f"Cannot create log directory: {str(e)}")

                if os.path.exists(log_dir):
                    if not os.access(log_dir, os.W_OK):
                        issues.append(f"Log directory not writable: {log_dir}")

            if issues:
                return HealthCheckResult(
                    name="permissions",
                    status=HealthStatus.CRITICAL,
                    message="; ".join(issues),
                    timestamp=time.time(),
                    duration_ms=0,
                    details={"issues": issues},
                )
            else:
                return HealthCheckResult(
                    name="permissions",
                    status=HealthStatus.HEALTHY,
                    message="All permissions are correct",
                    timestamp=time.time(),
                    duration_ms=0,
                    details={
                        "cache_dir": cache_dir,
                        "log_dir": log_dir if self.config.logging.file else None,
                    },
                )

        except Exception as e:
            return HealthCheckResult(
                name="permissions",
                status=HealthStatus.CRITICAL,
                message=f"Permissions check failed: {str(e)}",
                timestamp=time.time(),
                duration_ms=0,
                details={"exception": str(e)},
            )

    def start_monitoring(self, interval: int = 30):
        """Start application monitoring."""
        self.system_monitor.start_monitoring(interval)
        self.logger.info("Application monitoring started")

    def stop_monitoring(self):
        """Stop application monitoring."""
        self.system_monitor.stop_monitoring()
        self.logger.info("Application monitoring stopped")

    def get_health_status(self) -> Dict[str, Any]:
        """Get complete health status."""
        overall_health = self.health_checker.get_overall_health()
        system_metrics = self.metrics_collector.get_aggregated_metrics()

        return {
            "overall": overall_health.to_dict(),
            "checks": {
                name: result.to_dict()
                for name, result in self.health_checker.last_results.items()
            },
            "metrics": system_metrics,
            "timestamp": time.time(),
        }

    def record_request_metric(self, endpoint: str, duration_ms: float, status: str):
        """Record request metrics."""
        self.metrics_collector.increment_counter(
            "requests.total", tags={"endpoint": endpoint, "status": status}
        )
        self.metrics_collector.record_timer(
            "requests.duration_ms", duration_ms, tags={"endpoint": endpoint}
        )

    def record_transcription_metric(
        self, duration_ms: float, text_length: int, success: bool
    ):
        """Record transcription metrics."""
        self.metrics_collector.record_timer("transcription.duration_ms", duration_ms)
        self.metrics_collector.set_gauge("transcription.text_length", text_length)
        self.metrics_collector.increment_counter(
            "transcription.total", tags={"success": str(success)}
        )


# Global application monitor instance
_app_monitor = None


def get_app_monitor() -> ApplicationMonitor:
    """Get global application monitor instance."""
    global _app_monitor
    if _app_monitor is None:
        _app_monitor = ApplicationMonitor()
    return _app_monitor


def start_monitoring(interval: int = 30):
    """Start global monitoring."""
    get_app_monitor().start_monitoring(interval)


def stop_monitoring():
    """Stop global monitoring."""
    get_app_monitor().stop_monitoring()


def get_health_status() -> Dict[str, Any]:
    """Get global health status."""
    return get_app_monitor().get_health_status()


if __name__ == "__main__":
    # Example usage
    monitor = ApplicationMonitor()

    # Start monitoring
    monitor.start_monitoring(interval=5)

    # Get health status
    health = monitor.get_health_status()
    print(f"Health status: {json.dumps(health, indent=2)}")

    # Record some metrics
    monitor.record_request_metric("transcribe", 1500, "success")
    monitor.record_transcription_metric(1200, 150, True)

    # Wait a bit and get updated status
    time.sleep(6)
    health = monitor.get_health_status()
    print(f"Updated health status: {json.dumps(health, indent=2)}")

    # Stop monitoring
    monitor.stop_monitoring()
