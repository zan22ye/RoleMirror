import json
import os
from typing import List, Dict, Any

class SafetyChecker:
    def __init__(self, blocked_words_path: str = "src/data/blocked_words.json"):
        self.blocked_words = []
        try:
            if os.path.exists(blocked_words_path):
                with open(blocked_words_path, 'r', encoding='utf-8') as f:
                    self.blocked_words = json.load(f)
            else:
                print(f"Warning: Blocked words file not found at {blocked_words_path}")
        except Exception as e:
            print(f"Error loading blocked words: {e}")

    def check(self, text: str) -> Dict[str, Any]:
        """
        Check text for blocked words.
        Returns a dict with 'is_safe' (bool) and 'violations' (list of found words).
        """
        violations = []
        for word in self.blocked_words:
            if word in text:
                violations.append(word)
        
        return {
            "is_safe": len(violations) == 0,
            "violations": violations
        }

    def check_transcript(self, transcript: List[str]) -> Dict[str, Any]:
        """
        Check an entire transcript (list of strings) for violations.
        Only checks NPC responses (assuming format 'NPC: ...').
        """
        all_violations = []
        safe = True
        
        for line in transcript:
            if line.startswith("NPC:"):
                content = line[4:].strip()
                result = self.check(content)
                if not result['is_safe']:
                    safe = False
                    all_violations.extend(result['violations'])
        
        return {
            "is_safe": safe,
            "violations": list(set(all_violations)) # Unique violations
        }
