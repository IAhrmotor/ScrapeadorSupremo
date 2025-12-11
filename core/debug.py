"""
Debug system for tracking code flow throughout the application.

Provides comprehensive logging, flow tracking, and execution tracing
for all agents and orchestrator operations.
"""

import functools
import inspect
import time
import traceback
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path


class DebugLevel(IntEnum):
    """Debug verbosity levels."""
    OFF = 0
    ERROR = 1      # Only errors
    WARN = 2       # Errors + warnings
    INFO = 3       # Normal flow info
    DEBUG = 4      # Detailed debugging
    TRACE = 5      # Everything including function entry/exit


@dataclass
class FlowEntry:
    """Represents a single entry in the execution flow."""
    timestamp: datetime
    level: DebugLevel
    component: str
    action: str
    message: str
    data: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    call_stack: Optional[List[str]] = None


@dataclass
class ExecutionContext:
    """Tracks the current execution context."""
    task_id: str
    start_time: datetime
    agent_chain: List[str] = field(default_factory=list)
    department: Optional[str] = None
    flow: List[FlowEntry] = field(default_factory=list)


class Debug:
    """
    Centralized debug system for tracking code flow.

    Features:
    - Multi-level logging (ERROR, WARN, INFO, DEBUG, TRACE)
    - Execution flow tracking
    - Function call tracing with decorators
    - Performance timing
    - Call stack capture
    - Agent chain tracking
    """

    _instance: Optional['Debug'] = None

    def __new__(cls) -> 'Debug':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.level = DebugLevel.INFO
        self.enabled = True
        self._contexts: Dict[str, ExecutionContext] = {}
        self._current_context: Optional[str] = None
        self._global_flow: List[FlowEntry] = []
        self._start_time = datetime.now()
        self._initialized = True

        # Output settings
        self.show_timestamps = True
        self.show_file_info = True
        self.show_call_stack = False
        self.colorize = True
        self.log_to_file = False
        self.log_file_path: Optional[Path] = None

    def set_level(self, level: DebugLevel) -> None:
        """Set the debug level."""
        self.level = level

    def enable(self) -> None:
        """Enable debugging."""
        self.enabled = True

    def disable(self) -> None:
        """Disable debugging."""
        self.enabled = False

    def _get_caller_info(self, depth: int = 3) -> tuple:
        """Get caller file and line number."""
        frame = inspect.currentframe()
        for _ in range(depth):
            if frame is not None:
                frame = frame.f_back

        if frame:
            return (frame.f_code.co_filename, frame.f_lineno)
        return (None, None)

    def _get_call_stack(self, depth: int = 10) -> List[str]:
        """Get the current call stack."""
        stack = traceback.extract_stack()[:-3][-depth:]
        return [f"{s.filename}:{s.lineno} in {s.name}" for s in stack]

    def _format_message(self, entry: FlowEntry) -> str:
        """Format a flow entry for output."""
        parts = []

        # Level badge with color
        level_badges = {
            DebugLevel.ERROR: "[ERROR]",
            DebugLevel.WARN: "[WARN]",
            DebugLevel.INFO: "[INFO]",
            DebugLevel.DEBUG: "[DEBUG]",
            DebugLevel.TRACE: "[TRACE]",
        }
        parts.append(level_badges.get(entry.level, "[???]"))

        # Timestamp
        if self.show_timestamps:
            parts.append(entry.timestamp.strftime("%H:%M:%S.%f")[:-3])

        # Component
        parts.append(f"[{entry.component}]")

        # Action
        if entry.action:
            parts.append(f"<{entry.action}>")

        # Message
        parts.append(entry.message)

        # Duration
        if entry.duration_ms is not None:
            parts.append(f"({entry.duration_ms:.2f}ms)")

        # File info
        if self.show_file_info and entry.file_path:
            filename = Path(entry.file_path).name
            parts.append(f"@ {filename}:{entry.line_number}")

        return " ".join(parts)

    def _log(
        self,
        level: DebugLevel,
        component: str,
        action: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        """Internal logging method."""
        if not self.enabled or level > self.level:
            return

        file_path, line_number = self._get_caller_info()
        call_stack = self._get_call_stack() if self.show_call_stack else None

        entry = FlowEntry(
            timestamp=datetime.now(),
            level=level,
            component=component,
            action=action,
            message=message,
            data=data,
            duration_ms=duration_ms,
            file_path=file_path,
            line_number=line_number,
            call_stack=call_stack
        )

        # Add to global flow
        self._global_flow.append(entry)

        # Add to current context if exists
        if self._current_context and self._current_context in self._contexts:
            self._contexts[self._current_context].flow.append(entry)

        # Print
        print(self._format_message(entry))

        # Data details at DEBUG level
        if data and self.level >= DebugLevel.DEBUG:
            for key, value in data.items():
                print(f"    {key}: {value}")

        # Call stack at TRACE level
        if call_stack and self.level >= DebugLevel.TRACE:
            print("    Call stack:")
            for frame in call_stack:
                print(f"      -> {frame}")

    # === Public logging methods ===

    def error(self, component: str, message: str, data: Optional[Dict] = None) -> None:
        """Log an error."""
        self._log(DebugLevel.ERROR, component, "error", message, data)

    def warn(self, component: str, message: str, data: Optional[Dict] = None) -> None:
        """Log a warning."""
        self._log(DebugLevel.WARN, component, "warn", message, data)

    def info(self, component: str, message: str, data: Optional[Dict] = None) -> None:
        """Log info."""
        self._log(DebugLevel.INFO, component, "info", message, data)

    def debug(self, component: str, message: str, data: Optional[Dict] = None) -> None:
        """Log debug info."""
        self._log(DebugLevel.DEBUG, component, "debug", message, data)

    def trace(self, component: str, message: str, data: Optional[Dict] = None) -> None:
        """Log trace info."""
        self._log(DebugLevel.TRACE, component, "trace", message, data)

    # === Flow tracking ===

    def flow_start(self, component: str, action: str, data: Optional[Dict] = None) -> float:
        """Mark the start of a flow action. Returns start time for timing."""
        self._log(DebugLevel.INFO, component, f"{action}:START", f"Starting {action}", data)
        return time.perf_counter()

    def flow_end(self, component: str, action: str, start_time: float, data: Optional[Dict] = None) -> None:
        """Mark the end of a flow action with timing."""
        duration_ms = (time.perf_counter() - start_time) * 1000
        self._log(DebugLevel.INFO, component, f"{action}:END", f"Completed {action}", data, duration_ms)

    def flow_step(self, component: str, step: str, message: str, data: Optional[Dict] = None) -> None:
        """Log a step in the current flow."""
        self._log(DebugLevel.INFO, component, f"step:{step}", message, data)

    # === Context management ===

    def start_context(self, task_id: str, department: Optional[str] = None) -> None:
        """Start a new execution context."""
        self._contexts[task_id] = ExecutionContext(
            task_id=task_id,
            start_time=datetime.now(),
            department=department
        )
        self._current_context = task_id
        self.info("context", f"Started context: {task_id}", {"department": department})

    def end_context(self, task_id: str) -> Optional[ExecutionContext]:
        """End an execution context and return it."""
        if task_id in self._contexts:
            ctx = self._contexts.pop(task_id)
            if self._current_context == task_id:
                self._current_context = None
            self.info("context", f"Ended context: {task_id}")
            return ctx
        return None

    def add_to_agent_chain(self, agent_name: str) -> None:
        """Add an agent to the current context's chain."""
        if self._current_context and self._current_context in self._contexts:
            self._contexts[self._current_context].agent_chain.append(agent_name)
            self.debug("context", f"Agent added to chain: {agent_name}")

    # === Reporting ===

    def get_flow_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution flow."""
        total_time = (datetime.now() - self._start_time).total_seconds()

        level_counts = {level.name: 0 for level in DebugLevel if level != DebugLevel.OFF}
        components = set()

        for entry in self._global_flow:
            level_counts[entry.level.name] += 1
            components.add(entry.component)

        return {
            "total_entries": len(self._global_flow),
            "total_time_seconds": total_time,
            "level_counts": level_counts,
            "components": list(components),
            "active_contexts": list(self._contexts.keys())
        }

    def print_flow_report(self) -> None:
        """Print a formatted flow report."""
        summary = self.get_flow_summary()

        print("\n" + "=" * 60)
        print("EXECUTION FLOW REPORT")
        print("=" * 60)
        print(f"Total entries: {summary['total_entries']}")
        print(f"Total time: {summary['total_time_seconds']:.2f}s")
        print(f"Components: {', '.join(summary['components'])}")
        print("\nLevel breakdown:")
        for level, count in summary['level_counts'].items():
            if count > 0:
                print(f"  {level}: {count}")
        print("=" * 60)

    def clear(self) -> None:
        """Clear all flow data."""
        self._global_flow.clear()
        self._contexts.clear()
        self._current_context = None
        self._start_time = datetime.now()


# === Decorators ===

def debug_flow(component: Optional[str] = None):
    """
    Decorator to automatically trace function entry/exit.

    Usage:
        @debug_flow("my_component")
        def my_function(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        comp = component or func.__module__.split('.')[-1]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            debugger = get_debugger()
            func_name = func.__name__

            # Log entry
            debugger.trace(comp, f"ENTER {func_name}", {
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100]
            })

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000

                # Log exit
                debugger.trace(comp, f"EXIT {func_name}", {
                    "result": str(result)[:100],
                    "duration_ms": f"{duration:.2f}"
                })

                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                debugger.error(comp, f"EXCEPTION in {func_name}: {e}", {
                    "duration_ms": f"{duration:.2f}",
                    "exception": str(e)
                })
                raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            debugger = get_debugger()
            func_name = func.__name__

            debugger.trace(comp, f"ENTER {func_name} (async)", {
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100]
            })

            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start) * 1000

                debugger.trace(comp, f"EXIT {func_name} (async)", {
                    "result": str(result)[:100],
                    "duration_ms": f"{duration:.2f}"
                })

                return result
            except Exception as e:
                duration = (time.perf_counter() - start) * 1000
                debugger.error(comp, f"EXCEPTION in {func_name}: {e}", {
                    "duration_ms": f"{duration:.2f}",
                    "exception": str(e)
                })
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


# === Global instance ===

_debugger: Optional[Debug] = None

def get_debugger() -> Debug:
    """Get the global debugger instance."""
    global _debugger
    if _debugger is None:
        _debugger = Debug()
    return _debugger
