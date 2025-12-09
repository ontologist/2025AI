"""Lightweight resource monitor for gating assignment grading."""
import psutil
from app.core.config import settings


class ResourceMonitor:
    """Check CPU and memory utilization against a configurable threshold."""

    def __init__(self, limit: float | None = None):
        self.limit = limit if limit is not None else settings.ASSIGNMENT_RESOURCE_LIMIT

    def is_overloaded(self) -> bool:
        """
        Return True if both CPU and memory usage meet or exceed the limit.
        This keeps grading paused only when the system is under noticeable load.
        """
        try:
            cpu = psutil.cpu_percent(interval=0.1) / 100.0
            mem = psutil.virtual_memory().percent / 100.0
            return cpu >= self.limit and mem >= self.limit
        except Exception:
            # If psutil is unavailable or any error occurs, fail open (not overloaded)
            return False

