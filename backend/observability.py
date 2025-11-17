"""
Observability System: Logging, Tracing, and Metrics
Comprehensive monitoring and observability for the multi-agent system
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import threading
from contextlib import contextmanager

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        if hasattr(record, 'span_id'):
            log_entry['span_id'] = record.span_id
        if hasattr(record, 'agent_id'):
            log_entry['agent_id'] = record.agent_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
            
        return json.dumps(log_entry)

# Tracing System
@dataclass
class Span:
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = ""
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"
    
    def finish(self):
        self.end_time = time.time()
        self.status = "finished"
    
    def duration(self) -> float:
        end = self.end_time or time.time()
        return end - self.start_time
    
    def add_tag(self, key: str, value: Any):
        self.tags[key] = value
    
    def log(self, message: str, **kwargs):
        log_entry = {
            'timestamp': time.time(),
            'message': message,
            **kwargs
        }
        self.logs.append(log_entry)

class Tracer:
    def __init__(self):
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, str] = {}  # thread_id -> span_id
        self.traces: Dict[str, List[str]] = defaultdict(list)  # trace_id -> span_ids
    
    def start_span(self, operation_name: str, parent_span: Optional[Span] = None, trace_id: str = None) -> Span:
        thread_id = str(threading.get_ident())
        
        if trace_id is None:
            if parent_span:
                trace_id = parent_span.trace_id
            else:
                trace_id = str(uuid.uuid4())
        
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span.span_id if parent_span else None,
            operation_name=operation_name
        )
        
        self.spans[span.span_id] = span
        self.active_spans[thread_id] = span.span_id
        self.traces[trace_id].append(span.span_id)
        
        return span
    
    def get_active_span(self) -> Optional[Span]:
        thread_id = str(threading.get_ident())
        span_id = self.active_spans.get(thread_id)
        return self.spans.get(span_id) if span_id else None
    
    def finish_span(self, span: Span):
        span.finish()
        thread_id = str(threading.get_ident())
        if self.active_spans.get(thread_id) == span.span_id:
            del self.active_spans[thread_id]
    
    @contextmanager
    def trace(self, operation_name: str, **tags):
        span = self.start_span(operation_name)
        for key, value in tags.items():
            span.add_tag(key, value)
        
        try:
            yield span
        except Exception as e:
            span.add_tag("error", True)
            span.add_tag("error.message", str(e))
            span.log("Exception occurred", error=str(e))
            raise
        finally:
            self.finish_span(span)
    
    def get_trace(self, trace_id: str) -> List[Span]:
        span_ids = self.traces.get(trace_id, [])
        return [self.spans[span_id] for span_id in span_ids if span_id in self.spans]

# Metrics System
class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Metric:
    name: str
    metric_type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if isinstance(self.metric_type, str):
            self.metric_type = MetricType(self.metric_type)

class MetricsCollector:
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.counters[key] += value
        
        metric = Metric(name, MetricType.COUNTER, self.counters[key], labels)
        self.metrics[name].append(metric)
    
    def gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.gauges[key] = value
        
        metric = Metric(name, MetricType.GAUGE, value, labels)
        self.metrics[name].append(metric)
    
    def histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value"""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.histograms[key].append(value)
        
        metric = Metric(name, MetricType.HISTOGRAM, value, labels)
        self.metrics[name].append(metric)
    
    def timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """Record a timer value"""
        labels = labels or {}
        key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.timers[key].append(duration)
        
        metric = Metric(name, MetricType.TIMER, duration, labels)
        self.metrics[name].append(metric)
    
    @contextmanager
    def time_operation(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.timer(name, duration, labels)
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if name not in self.metrics:
            return {}
        
        recent_metrics = self.metrics[name][-100:]  # Last 100 values
        
        if not recent_metrics:
            return {}
        
        metric_type = recent_metrics[0].metric_type
        values = [m.value for m in recent_metrics]
        
        summary = {
            "name": name,
            "type": metric_type.value,
            "count": len(values),
            "latest": values[-1] if values else 0,
            "timestamp": recent_metrics[-1].timestamp if recent_metrics else 0
        }
        
        if metric_type in [MetricType.HISTOGRAM, MetricType.TIMER]:
            summary.update({
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "p50": self._percentile(values, 50),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99)
            })
        
        return summary
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics"""
        return {name: self.get_metric_summary(name) for name in self.metrics.keys()}

# Agent-specific observability
class AgentObserver:
    def __init__(self, agent_id: str, tracer: Tracer, metrics: MetricsCollector):
        self.agent_id = agent_id
        self.tracer = tracer
        self.metrics = metrics
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger for the agent"""
        logger = logging.getLogger(f"agent.{self.agent_id}")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def log(self, level: str, message: str, **kwargs):
        """Log with agent context"""
        extra = {
            'agent_id': self.agent_id,
            **kwargs
        }
        
        # Add tracing context if available
        active_span = self.tracer.get_active_span()
        if active_span:
            extra['trace_id'] = active_span.trace_id
            extra['span_id'] = active_span.span_id
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def start_operation(self, operation_name: str, **tags) -> Span:
        """Start a traced operation"""
        span = self.tracer.start_span(f"{self.agent_id}.{operation_name}")
        span.add_tag("agent_id", self.agent_id)
        
        for key, value in tags.items():
            span.add_tag(key, value)
        
        self.metrics.counter("agent.operations.started", labels={"agent_id": self.agent_id, "operation": operation_name})
        return span
    
    def record_metric(self, metric_name: str, value: float, metric_type: str = "gauge", **labels):
        """Record a metric with agent context"""
        labels["agent_id"] = self.agent_id
        
        if metric_type == "counter":
            self.metrics.counter(metric_name, value, labels)
        elif metric_type == "gauge":
            self.metrics.gauge(metric_name, value, labels)
        elif metric_type == "histogram":
            self.metrics.histogram(metric_name, value, labels)
        elif metric_type == "timer":
            self.metrics.timer(metric_name, value, labels)

# System-wide observability
class ObservabilityManager:
    def __init__(self):
        self.tracer = Tracer()
        self.metrics = MetricsCollector()
        self.agent_observers: Dict[str, AgentObserver] = {}
        self.system_logger = self._setup_system_logger()
        self.alert_rules: List[Dict[str, Any]] = []
        self.dashboards: Dict[str, Dict[str, Any]] = {}
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_system_logger(self) -> logging.Logger:
        """Setup system-wide logger"""
        logger = logging.getLogger("multi_agent_system")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    def get_agent_observer(self, agent_id: str) -> AgentObserver:
        """Get or create observer for an agent"""
        if agent_id not in self.agent_observers:
            self.agent_observers[agent_id] = AgentObserver(agent_id, self.tracer, self.metrics)
        
        return self.agent_observers[agent_id]
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        def metrics_collector():
            # Background thread for collecting metrics
            # Runs forever until the app shuts down
            while True:
                try:
                    # Collect system metrics
                    self.metrics.gauge("system.active_agents", len(self.agent_observers))
                    self.metrics.gauge("system.active_traces", len(self.tracer.traces))
                    self.metrics.gauge("system.total_spans", len(self.tracer.spans))
                    
                    # Check alert rules
                    self._check_alerts()
                    
                    time.sleep(10)  # Collect every 10 seconds
                except Exception as e:
                    self.system_logger.error(f"Metrics collection error: {e}")
        
        thread = threading.Thread(target=metrics_collector, daemon=True)
        thread.start()
    
    def add_alert_rule(self, name: str, condition: Callable[[Dict[str, Any]], bool], action: Callable[[], None]):
        """Add an alert rule"""
        self.alert_rules.append({
            "name": name,
            "condition": condition,
            "action": action,
            "last_triggered": None
        })
    
    def _check_alerts(self):
        """Check all alert rules
        
        This runs every 10 seconds which might be overkill.
        Should probably make this configurable.
        """
        current_metrics = self.metrics.get_all_metrics()
        
        for rule in self.alert_rules:
            try:
                if rule["condition"](current_metrics):
                    # Avoid spam - only trigger once per minute
                    last_triggered = rule.get("last_triggered")
                    if not last_triggered or time.time() - last_triggered > 60:
                        rule["action"]()
                        rule["last_triggered"] = time.time()
                        self.system_logger.warning(f"Alert triggered: {rule['name']}")
            except Exception as e:
                self.system_logger.error(f"Alert rule error: {e}")
    
    def create_dashboard(self, name: str, metrics: List[str], layout: Dict[str, Any] = None):
        """Create a monitoring dashboard"""
        self.dashboards[name] = {
            "metrics": metrics,
            "layout": layout or {"type": "grid", "columns": 2},
            "created_at": datetime.now().isoformat()
        }
    
    def get_dashboard_data(self, name: str) -> Dict[str, Any]:
        """Get data for a dashboard"""
        if name not in self.dashboards:
            return {}
        
        dashboard = self.dashboards[name]
        data = {}
        
        for metric_name in dashboard["metrics"]:
            data[metric_name] = self.metrics.get_metric_summary(metric_name)
        
        return {
            "dashboard": dashboard,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_trace_analysis(self, trace_id: str) -> Dict[str, Any]:
        """Get detailed trace analysis"""
        spans = self.tracer.get_trace(trace_id)
        
        if not spans:
            return {}
        
        # Build trace tree
        span_map = {span.span_id: span for span in spans}
        root_spans = [span for span in spans if span.parent_span_id is None]
        
        def build_tree(span):
            children = [s for s in spans if s.parent_span_id == span.span_id]
            return {
                "span": {
                    "span_id": span.span_id,
                    "operation_name": span.operation_name,
                    "duration": span.duration(),
                    "tags": span.tags,
                    "logs": span.logs,
                    "status": span.status
                },
                "children": [build_tree(child) for child in children]
            }
        
        trace_tree = [build_tree(root) for root in root_spans]
        
        # Calculate trace statistics
        total_duration = max(span.duration() for span in spans) if spans else 0
        total_spans = len(spans)
        error_spans = len([span for span in spans if span.tags.get("error")])
        
        return {
            "trace_id": trace_id,
            "total_duration": total_duration,
            "total_spans": total_spans,
            "error_spans": error_spans,
            "success_rate": (total_spans - error_spans) / total_spans if total_spans > 0 else 0,
            "trace_tree": trace_tree,
            "timeline": sorted([
                {
                    "span_id": span.span_id,
                    "operation_name": span.operation_name,
                    "start_time": span.start_time,
                    "end_time": span.end_time or span.start_time,
                    "duration": span.duration()
                }
                for span in spans
            ], key=lambda x: x["start_time"])
        }
    
    def export_metrics(self, format_type: str = "prometheus") -> str:
        """Export metrics in various formats"""
        if format_type == "prometheus":
            return self._export_prometheus_format()
        elif format_type == "json":
            return json.dumps(self.metrics.get_all_metrics(), indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format
        
        Had to look up the Prometheus format spec for this.
        Probably not 100% correct but works with Grafana.
        """
        lines = []
        
        for metric_name, summary in self.metrics.get_all_metrics().items():
            # Convert metric name to Prometheus format
            prom_name = metric_name.replace(".", "_").replace("-", "_")
            
            lines.append(f"# HELP {prom_name} {summary.get('type', 'gauge')} metric")
            lines.append(f"# TYPE {prom_name} {summary.get('type', 'gauge')}")
            
            if summary.get("type") == "histogram":
                # Export histogram buckets
                lines.append(f"{prom_name}_count {summary.get('count', 0)}")
                lines.append(f"{prom_name}_sum {summary.get('avg', 0) * summary.get('count', 0)}")
            else:
                lines.append(f"{prom_name} {summary.get('latest', 0)}")
        
        return "\n".join(lines)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        all_metrics = self.metrics.get_all_metrics()
        
        # Calculate health score based on error rates and performance
        error_rate = 0
        avg_response_time = 0
        
        if "agent.operations.errors" in all_metrics:
            total_ops = all_metrics.get("agent.operations.started", {}).get("latest", 1)
            total_errors = all_metrics.get("agent.operations.errors", {}).get("latest", 0)
            error_rate = total_errors / max(total_ops, 1)
        
        if "agent.response_time" in all_metrics:
            avg_response_time = all_metrics["agent.response_time"].get("avg", 0)
        
        health_score = max(0, 100 - (error_rate * 50) - min(avg_response_time / 10, 50))
        
        return {
            "health_score": health_score,
            "status": "healthy" if health_score > 80 else "degraded" if health_score > 50 else "unhealthy",
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "active_agents": len(self.agent_observers),
            "total_traces": len(self.tracer.traces),
            "metrics_collected": len(all_metrics),
            "timestamp": datetime.now().isoformat()
        }