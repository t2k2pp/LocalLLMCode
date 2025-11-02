"""
LocalLLM Code - Revolutionary Agentic Coding Tool
A paradigm-shifting development agent that understands your project's DNA
"""

__version__ = "1.0.0"
__author__ = "LocalLLM Code Team"

# Core imports for easy access
from .core.project_dna import ProjectDNA
from .core.context_manager import SmartContextManager

# Import other components with graceful fallback
__all__ = ["ProjectDNA", "SmartContextManager"]

try:
    from .agents.react_agent import ReActAgent
    from .agents.multi_agent import MultiAgentSystem, AgentRole
    __all__.extend(["ReActAgent", "MultiAgentSystem", "AgentRole"])
except ImportError as e:
    print(f"Warning: Could not import agents: {e}")

try:
    from .tools.tool_system import ToolSystem
    __all__.append("ToolSystem")
except ImportError as e:
    print(f"Warning: Could not import tools: {e}")

try:
    from .memory.external_memory import ExternalMemorySystem
    __all__.append("ExternalMemorySystem")
except ImportError as e:
    print(f"Warning: Could not import memory: {e}")

try:
    from .llm.clients import LLMClient
    from .llm.analyzers import ProjectAnalyzer
    __all__.extend(["LLMClient", "ProjectAnalyzer"])
except ImportError as e:
    print(f"Warning: Could not import LLM components: {e}")