from typing import Dict, Callable, Any
import sys


class WorkerRegistry:
    """
    Global registry for Temporal workers.
    
    This class maintains a dictionary of registered workers and provides
    methods to register and retrieve workers.
    """
    
    def __init__(self):
        self._workers: Dict[str, Any] = {}
    
    def register(self, name: str, worker_func: Callable) -> None:
        """
        Register a worker function with the given name.
        
        Args:
            name: The name to register the worker under (e.g., "trend_analyzer_worker")
            worker_func: The async worker function to register
        """
        if name in self._workers:
            print(f"WARNING: Worker '{name}' is already registered. Overwriting.", file=sys.stderr, flush=True)
        
        self._workers[name] = worker_func
    
    def get(self, name: str):
        """
        Get a registered worker by name.
        
        Args:
            name: The name of the worker to retrieve
            
        Returns:
            The worker function if found, None otherwise
        """
        return self._workers.get(name)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all registered workers.
        
        Returns:
            Dictionary of all registered workers
        """
        return self._workers.copy()
    
    def list_workers(self) -> list[str]:
        """
        Get a list of all registered worker names.
        
        Returns:
            List of worker names
        """
        return list(self._workers.keys())

_global_registry = WorkerRegistry()

def register_worker(name: str):
    """
    Decorator to register a worker function in the global registry.
    
    Usage:
        @register_worker("my_worker")
        async def my_worker():
            # Worker implementation
            pass
    
    Args:
        name: The name to register the worker under
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        _global_registry.register(name, func)
        return func
    return decorator


def get_worker(name: str) -> Callable | None:
    """
    Get a registered worker by name.
    
    Args:
        name: The name of the worker to retrieve
        
    Returns:
        The worker function if found, None otherwise
    """
    return _global_registry.get(name)


def get_all_workers() -> Dict[str, Callable]:
    """
    Get all registered workers.
    
    Returns:
        Dictionary of all registered workers
    """
    return _global_registry.get_all()


def list_worker_names() -> list[str]:
    """
    Get a list of all registered worker names.
    
    Returns:
        List of worker names
    """
    return _global_registry.list_workers()


# For backward compatibility, expose the workers dict
workers = _global_registry.get_all()

