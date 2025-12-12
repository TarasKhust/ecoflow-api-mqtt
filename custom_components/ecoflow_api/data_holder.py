"""Data holder for diagnostic mode - stores recent messages."""
from __future__ import annotations

from typing import Any, TypeVar

_T = TypeVar("_T")


class BoundFifoList(list[_T]):
    """Fixed-size FIFO list for storing recent messages.
    
    This is used in diagnostic mode to store recent REST requests,
    MQTT messages, and command responses for debugging purposes.
    
    Attributes:
        maxlen: Maximum number of items to store
    """
    
    def __init__(self, maxlen: int = 20) -> None:
        """Initialize the FIFO list.
        
        Args:
            maxlen: Maximum number of items to store (default: 20)
        """
        super().__init__()
        self.maxlen = maxlen
    
    def append(self, item: _T) -> None:
        """Append item to the list, removing oldest if at maxlen.
        
        Args:
            item: Item to append
        """
        super().insert(0, item)
        while len(self) >= self.maxlen:
            self.pop()

