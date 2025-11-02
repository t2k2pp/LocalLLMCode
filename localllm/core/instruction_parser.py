"""Instruction parser for structured guidelines and multi-step tasks"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class StructuredInstruction:
    """構造化された指示"""
    type: str  # "numbered_list", "table", "step_sequence"
    items: List[Dict[str, Any]]
    naming_pattern: Optional[str] = None
    directory_structure: Optional[Dict[str, Any]] = None
    required_files: Optional[List[str]] = None

class InstructionParser:
    """ガイドライン文書から構造化された指示を解析"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
    
    def parse_guideline_file(self, file_content: str) -> StructuredInstruction:
        """ガイドラインファイルの内容を解析"""
        
        # テーブル形式の検出
        table_instruction = self._parse_table_format(file_content)
        if table_instruction:
            return table_instruction
        
        # 番号付きリストの検出
        numbered_instruction = self._parse_numbered_list(file_content)
        if numbered_instruction:
            return numbered_instruction
        
        # ステップシーケンスの検出
        step_instruction = self._parse_step_sequence(file_content)
        if step_instruction:
            return step_instruction
        
        # デフォルト：一般的な指示
        return StructuredInstruction(
            type="general",
            items=[{"content": file_content}]
        )
    
    def _parse_table_format(self, content: str) -> Optional[StructuredInstruction]:
        """Markdownテーブル形式の解析"""
        
        # テーブルパターンの検出
        table_pattern = r'\|.*?\|.*?\|.*?\|.*?\|.*?\|'
        table_matches = re.findall(table_pattern, content, re.MULTILINE)
        
        if len(table_matches) < 3:  # ヘッダー + 区切り + データが最低必要
            return None
        
        # テーブル解析
        items = []
        lines = content.split('\n')
        in_table = False
        headers = []
        
        for line in lines:
            if '|' in line and '---' not in line:
                if not in_table:
                    # ヘッダー行
                    headers = [h.strip() for h in line.split('|')[1:-1] if h.strip()]
                    in_table = True
                    continue
                
                # データ行
                cells = [c.strip() for c in line.split('|')[1:-1] if c.strip()]
                if len(cells) >= len(headers):
                    item = {}
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            # Markdown装飾を除去
                            clean_cell = re.sub(r'\*\*(.*?)\*\*', r'\1', cells[i])
                            clean_cell = re.sub(r'`(.*?)`', r'\1', clean_cell)
                            item[header.lower().replace('**', '')] = clean_cell
                    items.append(item)
            elif in_table and '|' not in line:
                break
        
        if not items:
            return None
        
        # 番号とディレクトリ命名パターンの検出
        naming_pattern = self._extract_naming_pattern(content)
        directory_structure = self._extract_directory_structure(content)
        required_files = self._extract_required_files(content)
        
        return StructuredInstruction(
            type="table",
            items=items,
            naming_pattern=naming_pattern,
            directory_structure=directory_structure,
            required_files=required_files
        )
    
    def _parse_numbered_list(self, content: str) -> Optional[StructuredInstruction]:
        """番号付きリストの解析"""
        
        # 番号付きリストパターン
        numbered_pattern = r'^(\d+)\.?\s+(.+)$'
        items = []
        
        for line in content.split('\n'):
            match = re.match(numbered_pattern, line.strip())
            if match:
                number, text = match.groups()
                items.append({
                    'number': int(number),
                    'content': text.strip()
                })
        
        if not items:
            return None
        
        return StructuredInstruction(
            type="numbered_list",
            items=items,
            naming_pattern=self._extract_naming_pattern(content),
            directory_structure=self._extract_directory_structure(content),
            required_files=self._extract_required_files(content)
        )
    
    def _parse_step_sequence(self, content: str) -> Optional[StructuredInstruction]:
        """ステップシーケンスの解析"""
        
        # ステップパターンの検出
        step_patterns = [
            r'(?:ステップ|Step)\s*(\d+)[:\s]+(.+)',
            r'(\d+)\.\s*(.+)',
            r'^-\s+(.+)$'  # 箇条書き
        ]
        
        items = []
        step_number = 1
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            for pattern in step_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        number, text = match.groups()
                        items.append({
                            'number': int(number) if number.isdigit() else step_number,
                            'content': text.strip()
                        })
                    else:
                        items.append({
                            'number': step_number,
                            'content': match.group(1).strip()
                        })
                    step_number += 1
                    break
        
        if not items:
            return None
        
        return StructuredInstruction(
            type="step_sequence",
            items=items,
            naming_pattern=self._extract_naming_pattern(content),
            directory_structure=self._extract_directory_structure(content),
            required_files=self._extract_required_files(content)
        )
    
    def _extract_naming_pattern(self, content: str) -> Optional[str]:
        """命名パターンの抽出"""
        
        # よくある命名パターン
        patterns = [
            r'番号に対応するフォルダ',
            r'(\d{4})\s*(?:フォルダ|ディレクトリ)',
            r'projects/(\d+)',
            r'0001.*0002',  # 連番の例
            r'(\d+)\s*番',
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if '0001' in content or '0002' in content:
                    return 'numeric_4digit'  # 4桁数字
                elif re.search(r'\d+番', content):
                    return 'numeric_simple'  # 単純な数字
                else:
                    return 'numeric_padded'  # ゼロパディング
        
        return None
    
    def _extract_directory_structure(self, content: str) -> Optional[Dict[str, Any]]:
        """ディレクトリ構造の抽出"""
        
        structure_patterns = [
            r'projects\s*配下',
            r'projects\s*フォルダ',
            r'projects/',
        ]
        
        for pattern in structure_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    'base_directory': 'projects',
                    'create_subdirectories': True
                }
        
        return None
    
    def _extract_required_files(self, content: str) -> Optional[List[str]]:
        """必要ファイルの抽出"""
        
        files = []
        
        # ファイル名パターンの検出
        file_patterns = [
            r'README\.md',
            r'requirements\.txt',
            r'main\.py',
            r'app\.py',
            r'ソースファイル',
        ]
        
        for pattern in file_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                if 'README' in pattern:
                    files.append('README.md')
                elif 'requirements' in pattern:
                    files.append('requirements.txt')
                elif 'main' in pattern:
                    files.append('main.py')
                elif 'app' in pattern:
                    files.append('app.py')
                elif 'ソースファイル' in pattern:
                    files.append('main.py')  # デフォルトのソースファイル
        
        return files if files else None
    
    def generate_directory_name(self, instruction: StructuredInstruction, item_number: int) -> str:
        """アイテム番号からディレクトリ名を生成"""
        
        if instruction.naming_pattern == 'numeric_4digit':
            return f"{item_number:04d}"
        elif instruction.naming_pattern == 'numeric_padded':
            return f"{item_number:03d}"
        elif instruction.naming_pattern == 'numeric_simple':
            return str(item_number)
        else:
            # デフォルト：4桁ゼロパディング
            return f"{item_number:04d}"
    
    def get_file_content_requirements(self, instruction: StructuredInstruction, item: Dict[str, Any]) -> Dict[str, str]:
        """ファイル内容の要件を取得"""
        
        requirements = {}
        
        if instruction.required_files:
            for file_name in instruction.required_files:
                if file_name == 'README.md':
                    requirements[file_name] = self._generate_readme_requirements(item)
                elif file_name == 'requirements.txt':
                    requirements[file_name] = self._generate_requirements_txt(item)
                elif file_name in ['main.py', 'app.py']:
                    requirements[file_name] = self._generate_source_requirements(item)
        
        return requirements
    
    def _generate_readme_requirements(self, item: Dict[str, Any]) -> str:
        """README.mdの要件生成"""
        app_name = item.get('アプリ案', item.get('app案', item.get('content', 'Unknown App')))
        description = item.get('解決する課題', item.get('description', ''))
        
        return f"""# {app_name}

## 概要
{description}

## 起動方法
1. 必要なライブラリをインストール: `pip install -r requirements.txt`
2. アプリを実行: `python main.py`

## 利用手順
[具体的な使用方法を記載]
"""
    
    def _generate_requirements_txt(self, item: Dict[str, Any]) -> str:
        """requirements.txtの要件生成"""
        
        # 実装方向性からライブラリを抽出
        implementation = item.get('実装の方向性 (ライブラリ)', item.get('implementation', ''))
        
        libraries = []
        if 'tkinter' in implementation.lower():
            pass  # tkinterは標準ライブラリ
        if 'streamlit' in implementation.lower():
            libraries.append('streamlit')
        if 'pypdf' in implementation.lower():
            libraries.append('pypdf')
        if 'pillow' in implementation.lower():
            libraries.append('Pillow')
        if 'pandas' in implementation.lower():
            libraries.append('pandas')
        if 'openpyxl' in implementation.lower():
            libraries.append('openpyxl')
        if 'requests' in implementation.lower():
            libraries.append('requests')
        
        return '\n'.join(libraries) if libraries else '# No external dependencies required'
    
    def _generate_source_requirements(self, item: Dict[str, Any]) -> str:
        """ソースファイルの要件生成"""
        app_name = item.get('アプリ案', item.get('app案', item.get('content', 'Unknown App')))
        description = item.get('解決する課題', item.get('description', ''))
        
        return f'''"""
{app_name}

{description}
"""

def main():
    """メイン関数"""
    print(f"Starting {app_name}...")
    # TODO: 実装を追加
    pass

if __name__ == "__main__":
    main()
'''