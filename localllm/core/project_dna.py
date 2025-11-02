"""Project DNA analysis system"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class ProjectDNA:
    """プロジェクトの遺伝子情報 - 革新的なプロジェクト理解システム"""
    language: str
    frameworks: List[str]
    architecture_patterns: List[str]
    coding_style: Dict[str, Any]
    dependency_graph: Dict[str, List[str]]
    file_patterns: Dict[str, str]
    common_operations: List[str]
    last_updated: str
    complexity_score: float
    
    def to_context(self) -> str:
        """プロジェクトDNAをLLMコンテキストに変換"""
        return f"""
Project DNA Analysis:
- Primary Language: {self.language}
- Frameworks: {', '.join(self.frameworks)}
- Architecture: {', '.join(self.architecture_patterns)}
- Coding Style: {json.dumps(self.coding_style, indent=2)}
- Complexity Score: {self.complexity_score:.2f}/10.0
- Common Operations: {', '.join(self.common_operations[:5])}
"""