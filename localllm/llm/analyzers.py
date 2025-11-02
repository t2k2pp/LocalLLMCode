"""Project analysis system"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()
    
    class Progress:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def add_task(self, *args, **kwargs):
            return 1
        def update(self, *args, **kwargs):
            pass

from ..core.project_dna import ProjectDNA

class ProjectAnalyzer:
    """プロジェクトDNA分析エンジン"""
    
    def __init__(self):
        self.ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', '.DS_Store', '*.pyc', '*.log'
        }
    
    def analyze_project(self, root_path: Path) -> ProjectDNA:
        """プロジェクトの完全なDNA解析"""
        console.print("🧬 [bold cyan]Analyzing Project DNA...[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scanning project structure...", total=None)
            
            # ファイル収集
            all_files = list(self._scan_files(root_path))
            progress.update(task, description="Analyzing languages...")
            
            # 言語分析
            language = self._detect_primary_language(all_files)
            progress.update(task, description="Detecting frameworks...")
            
            # フレームワーク検出
            frameworks = self._detect_frameworks(all_files, root_path)
            progress.update(task, description="Analyzing architecture...")
            
            # アーキテクチャパターン
            patterns = self._detect_architecture_patterns(all_files, root_path)
            progress.update(task, description="Learning coding style...")
            
            # コーディングスタイル学習
            coding_style = self._learn_coding_style(all_files)
            progress.update(task, description="Building dependency graph...")
            
            # 依存関係グラフ
            dependency_graph = self._build_dependency_graph(all_files, root_path)
            progress.update(task, description="Calculating complexity...")
            
            # 複雑度計算
            complexity = self._calculate_complexity(all_files)
            
            progress.update(task, description="Complete!", completed=True)
        
        dna = ProjectDNA(
            language=language,
            frameworks=frameworks,
            architecture_patterns=patterns,
            coding_style=coding_style,
            dependency_graph=dependency_graph,
            file_patterns=self._extract_file_patterns(all_files),
            common_operations=self._extract_common_operations(all_files),
            last_updated=datetime.now().isoformat(),
            complexity_score=complexity
        )
        
        # DNAを保存
        self._save_dna(root_path, dna)
        
        return dna
    
    def _scan_files(self, root_path: Path):
        """プロジェクトファイルをスキャン"""
        for file_path in root_path.rglob('*'):
            if file_path.is_file() and not self._should_ignore(file_path):
                yield file_path
    
    def _should_ignore(self, file_path: Path) -> bool:
        """ファイルを無視すべきかチェック"""
        path_str = str(file_path)
        return any(pattern in path_str for pattern in self.ignore_patterns)
    
    def _detect_primary_language(self, files: List[Path]) -> str:
        """主要言語を検出"""
        extensions = {}
        for file_path in files:
            ext = file_path.suffix.lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
        
        if not extensions:
            return "unknown"
        
        # 最も多い拡張子から言語を推定
        primary_ext = max(extensions, key=extensions.get)
        
        lang_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
            '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP',
            '.jsx': 'React', '.tsx': 'TypeScript React', '.vue': 'Vue.js'
        }
        
        return lang_map.get(primary_ext, 'unknown')
    
    def _detect_frameworks(self, files: List[Path], root_path: Path) -> List[str]:
        """フレームワークを検出"""
        frameworks = []
        
        # 設定ファイルベースの検出
        config_files = {
            'package.json': self._detect_js_frameworks,
            'requirements.txt': self._detect_python_frameworks,
            'Pipfile': self._detect_python_frameworks,
            'pyproject.toml': self._detect_python_frameworks,
            'pom.xml': lambda x: ['Maven', 'Spring'],
            'build.gradle': lambda x: ['Gradle', 'Spring'],
            'Cargo.toml': lambda x: ['Rust'],
        }
        
        for file_path in files:
            if file_path.name in config_files:
                try:
                    detected = config_files[file_path.name](file_path)
                    if isinstance(detected, list):
                        frameworks.extend(detected)
                    else:
                        frameworks.extend(detected())
                except:
                    pass
        
        return list(set(frameworks))
    
    def _detect_js_frameworks(self, package_json_path: Path) -> List[str]:
        """package.jsonからJavaScriptフレームワークを検出"""
        try:
            with open(package_json_path, 'r') as f:
                data = json.load(f)
            
            frameworks = []
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            
            framework_map = {
                'react': 'React', 'vue': 'Vue.js', 'angular': 'Angular',
                'next': 'Next.js', 'nuxt': 'Nuxt.js', 'express': 'Express.js',
                'fastify': 'Fastify', 'nest': 'NestJS', 'svelte': 'Svelte'
            }
            
            for dep in deps:
                for fw_key, fw_name in framework_map.items():
                    if fw_key in dep.lower():
                        frameworks.append(fw_name)
            
            return frameworks
        except:
            return []
    
    def _detect_python_frameworks(self, requirements_path: Path) -> List[str]:
        """Pythonフレームワークを検出"""
        try:
            with open(requirements_path, 'r') as f:
                content = f.read().lower()
            
            frameworks = []
            framework_map = {
                'django': 'Django', 'flask': 'Flask', 'fastapi': 'FastAPI',
                'tornado': 'Tornado', 'pyramid': 'Pyramid', 'sanic': 'Sanic',
                'starlette': 'Starlette', 'quart': 'Quart'
            }
            
            for fw_key, fw_name in framework_map.items():
                if fw_key in content:
                    frameworks.append(fw_name)
            
            return frameworks
        except:
            return []
    
    def _detect_architecture_patterns(self, files: List[Path], root_path: Path) -> List[str]:
        """アーキテクチャパターンを検出"""
        patterns = []
        
        # ディレクトリ構造からパターンを推定
        dirs = {f.parent.name.lower() for f in files if f.parent != root_path}
        
        # MVC パターン
        if {'models', 'views', 'controllers'}.issubset(dirs):
            patterns.append('MVC')
        
        # Clean Architecture
        if {'domain', 'infrastructure', 'application'}.issubset(dirs):
            patterns.append('Clean Architecture')
        
        # Microservices
        if {'services', 'api', 'gateway'}.intersection(dirs):
            patterns.append('Microservices')
        
        # Component-based
        if {'components', 'containers', 'hooks'}.intersection(dirs):
            patterns.append('Component-based')
        
        return patterns
    
    def _learn_coding_style(self, files: List[Path]) -> Dict[str, Any]:
        """コーディングスタイルを学習"""
        style = {
            'indentation': 'spaces',
            'indent_size': 4,
            'max_line_length': 80,
            'naming_convention': 'snake_case',
            'documentation_style': 'docstring'
        }
        
        # 実際のファイルから学習
        try:
            python_files = [f for f in files if f.suffix == '.py']
            if python_files:
                sample_file = python_files[0]
                with open(sample_file, 'r') as f:
                    content = f.read()
                
                # インデント分析
                lines = content.split('\n')
                indented_lines = [line for line in lines if line.startswith((' ', '\t'))]
                
                if indented_lines:
                    first_indent = indented_lines[0]
                    if first_indent.startswith('\t'):
                        style['indentation'] = 'tabs'
                    else:
                        spaces = len(first_indent) - len(first_indent.lstrip())
                        style['indent_size'] = spaces
        except:
            pass
        
        return style
    
    def _build_dependency_graph(self, files: List[Path], root_path: Path) -> Dict[str, List[str]]:
        """依存関係グラフを構築"""
        graph = {}
        
        for file_path in files:
            if file_path.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    imports = self._extract_imports(content, file_path.suffix)
                    relative_path = str(file_path.relative_to(root_path))
                    graph[relative_path] = imports
                except:
                    continue
        
        return graph
    
    def _extract_imports(self, content: str, extension: str) -> List[str]:
        """ファイルからimport文を抽出"""
        imports = []
        
        if extension == '.py':
            # Python imports
            import_patterns = [
                r'from\s+(\S+)\s+import',
                r'import\s+(\S+)'
            ]
        elif extension in ['.js', '.ts', '.jsx', '.tsx']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import.*from\s+["\']([^"\']+)["\']',
                r'import\s+["\']([^"\']+)["\']'
            ]
        else:
            return imports
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return imports
    
    def _extract_file_patterns(self, files: List[Path]) -> Dict[str, str]:
        """ファイルパターンを抽出"""
        patterns = {}
        
        for file_path in files:
            ext = file_path.suffix
            if ext:
                patterns[ext] = patterns.get(ext, '') + f"{file_path.name} "
        
        return patterns
    
    def _extract_common_operations(self, files: List[Path]) -> List[str]:
        """よく使われる操作を抽出"""
        operations = [
            "add new feature", "fix bug", "refactor code", "update dependencies",
            "write tests", "improve performance", "add documentation"
        ]
        return operations
    
    def _calculate_complexity(self, files: List[Path]) -> float:
        """プロジェクトの複雑度を計算"""
        total_files = len(files)
        total_lines = 0
        
        for file_path in files[:50]:  # 最初の50ファイルをサンプリング
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            except:
                continue
        
        # 複雑度計算（ファイル数とコード行数を基準）
        complexity = min(10.0, (total_files / 100 + total_lines / 10000) * 5)
        return complexity
    
    def _save_dna(self, root_path: Path, dna: ProjectDNA):
        """プロジェクトDNAを保存"""
        dna_file = root_path / 'LOCALLLM.md'
        
        content = f"""# LocalLLM Code Project Memory

Generated: {dna.last_updated}

## Project DNA

{dna.to_context()}

## Project Structure
```
{self._generate_tree_structure(root_path)}
```

## Learning Notes
- This project follows {dna.language} conventions
- Architecture patterns: {', '.join(dna.architecture_patterns)}
- Complexity level: {dna.complexity_score:.1f}/10.0

## Common Operations
{chr(10).join(f"- {op}" for op in dna.common_operations)}

---
*This file is automatically generated and updated by LocalLLM Code*
"""
        
        with open(dna_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_tree_structure(self, root_path: Path, max_depth: int = 3) -> str:
        """プロジェクト構造を文字列として生成"""
        def build_tree(path: Path, prefix: str = "", depth: int = 0) -> str:
            if depth >= max_depth:
                return ""
            
            items = []
            try:
                children = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
                for i, child in enumerate(children[:10]):  # 最大10項目
                    if self._should_ignore(child):
                        continue
                    
                    is_last = i == len(children) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    items.append(f"{prefix}{current_prefix}{child.name}")
                    
                    if child.is_dir() and depth < max_depth - 1:
                        items.append(build_tree(child, prefix + next_prefix, depth + 1))
            except PermissionError:
                pass
            
            return "\n".join(filter(None, items))
        
        return build_tree(root_path)