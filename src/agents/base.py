from abc import ABC, abstractmethod
from typing import List, Dict

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.history: List[Dict[str, str]] = []

    @abstractmethod
    def chat(self, message: str) -> str:
        """
        Process an incoming message and return a response.
        """
        pass

    def get_history(self) -> List[Dict[str, str]]:
        return self.history
    
    def reset(self):
        self.history = []
