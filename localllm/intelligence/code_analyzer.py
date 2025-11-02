"""
Simple Code Analyzer - Lightweight code analysis for local LLM
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SimpleImprovement:
    """Simple improvement suggestion"""
    type: str
    line: int
    message: str
    severity: str  # 'info', 'warning', 'error'
    suggestion: str


@dataclass
class CodeMetrics:
    """Basic code metrics"""
    lines_of_code: int
    function_count: int
    class_count: int
    complexity_score: float
    max_function_length: int


class SimpleCodeAnalyzer:
    """Lightweight code analyzer optimized for local LLM context"""
    
    def __init__(self):
        self.supported_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx'}
    
    def can_analyze(self, file_path: Path) -> bool:
        """Check if file can be analyzed"""
        return file_path.suffix.lower() in self.supported_extensions
    
    def analyze_file(self, file_path: Path, content: str = None) -> Dict[str, Any]:
        """Analyze a single file for basic improvements"""
        if not self.can_analyze(file_path):
            return {'error': f'Unsupported file type: {file_path.suffix}'}
        
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return {'error': f'Failed to read file: {e}'}
        
        extension = file_path.suffix.lower()
        
        if extension == '.py':
            return self._analyze_python(content)
        elif extension in {'.js', '.ts', '.jsx', '.tsx'}:
            return self._analyze_javascript(content)
        
        return {'error': 'Analysis not implemented for this file type'}
    
    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Analyze Python code"""
        improvements = []
        metrics = self._get_python_metrics(content)
        
        # Basic checks
        lines = content.split('\n')
        
        # Check for long functions
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > 50:
                        improvements.append(SimpleImprovement(
                            type='long_function',
                            line=node.lineno,
                            message=f'Function "{node.name}" is {func_lines} lines long',
                            severity='warning',
                            suggestion='Consider breaking this function into smaller functions'
                        ))
        except SyntaxError:
            improvements.append(SimpleImprovement(
                type='syntax_error',
                line=1,
                message='File contains syntax errors',
                severity='error',
                suggestion='Fix syntax errors before analysis'
            ))
        
        # Check for unused imports (simple regex check)
        import_pattern = r'^import\s+(\w+)|^from\s+\w+\s+import\s+(\w+)'
        for i, line in enumerate(lines, 1):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)
                if module and content.count(module) == 1:  # Only appears in import
                    improvements.append(SimpleImprovement(
                        type='unused_import',
                        line=i,
                        message=f'Import "{module}" appears to be unused',
                        severity='info',
                        suggestion=f'Consider removing unused import: {module}'
                    ))
        
        # Check for magic numbers
        magic_number_pattern = r'\b\d{2,}\b'
        for i, line in enumerate(lines, 1):
            if re.search(magic_number_pattern, line) and '=' in line:
                improvements.append(SimpleImprovement(
                    type='magic_number',
                    line=i,
                    message='Possible magic number detected',
                    severity='info',
                    suggestion='Consider using named constants instead of magic numbers'
                ))
        
        return {
            'metrics': metrics,
            'improvements': improvements,
            'file_type': 'python'
        }
    
    def _analyze_javascript(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code"""
        improvements = []
        metrics = self._get_javascript_metrics(content)
        
        lines = content.split('\n')
        
        # Check for long functions (simple heuristic)
        in_function = False
        function_start = 0
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Detect function start
            if 'function' in stripped or '=>' in stripped:
                in_function = True
                function_start = i
                brace_count = 0
            
            if in_function:
                brace_count += stripped.count('{') - stripped.count('}')
                if brace_count <= 0 and i > function_start:
                    func_length = i - function_start
                    if func_length > 30:
                        improvements.append(SimpleImprovement(
                            type='long_function',
                            line=function_start,
                            message=f'Function is {func_length} lines long',
                            severity='warning',
                            suggestion='Consider breaking this function into smaller functions'
                        ))
                    in_function = False
        
        # Check for console.log statements
        for i, line in enumerate(lines, 1):
            if 'console.log' in line:
                improvements.append(SimpleImprovement(
                    type='debug_statement',
                    line=i,
                    message='console.log statement found',
                    severity='info',
                    suggestion='Remove debug statements before production'
                ))
        
        return {
            'metrics': metrics,
            'improvements': improvements,
            'file_type': 'javascript'
        }
    
    def _get_python_metrics(self, content: str) -> CodeMetrics:
        """Get basic metrics for Python code"""
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        
        function_count = 0
        class_count = 0
        max_function_length = 0
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_count += 1
                    func_length = node.end_lineno - node.lineno + 1
                    max_function_length = max(max_function_length, func_length)
                elif isinstance(node, ast.ClassDef):
                    class_count += 1
        except SyntaxError:
            pass
        
        # Simple complexity score based on metrics
        complexity_score = min(10.0, (loc / 100 + function_count / 10 + max_function_length / 20))
        
        return CodeMetrics(
            lines_of_code=loc,
            function_count=function_count,
            class_count=class_count,
            complexity_score=complexity_score,
            max_function_length=max_function_length
        )
    
    def _get_javascript_metrics(self, content: str) -> CodeMetrics:
        """Get basic metrics for JavaScript code"""
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        # Simple heuristics for JS
        function_count = content.count('function') + content.count('=>')
        class_count = content.count('class ')
        
        # Estimate max function length (rough)
        max_function_length = 0
        current_length = 0
        in_function = False
        
        for line in lines:
            if 'function' in line or '=>' in line:
                in_function = True
                current_length = 1
            elif in_function:
                current_length += 1
                if '}' in line and line.count('}') >= line.count('{'):
                    max_function_length = max(max_function_length, current_length)
                    in_function = False
                    current_length = 0
        
        complexity_score = min(10.0, (loc / 100 + function_count / 10 + max_function_length / 25))
        
        return CodeMetrics(
            lines_of_code=loc,
            function_count=function_count,
            class_count=class_count,
            complexity_score=complexity_score,
            max_function_length=max_function_length
        )
    
    def get_improvement_summary(self, improvements: List[SimpleImprovement]) -> str:
        """Generate a summary of improvements"""
        if not improvements:
            return "✅ No issues found. Code looks good!"
        
        by_severity = {}
        for imp in improvements:
            if imp.severity not in by_severity:
                by_severity[imp.severity] = []
            by_severity[imp.severity].append(imp)
        
        summary = []
        for severity in ['error', 'warning', 'info']:
            if severity in by_severity:
                count = len(by_severity[severity])
                emoji = {'error': '❌', 'warning': '⚠️', 'info': '💡'}[severity]
                summary.append(f"{emoji} {count} {severity}{'s' if count > 1 else ''}")
        
        return " | ".join(summary)