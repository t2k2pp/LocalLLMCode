"""File reference parser for natural language and @ notation"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class FileReferenceParser:
    """ファイル参照の自然言語解析とパース"""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        
        # ファイル参照パターン
        self.file_patterns = [
            # @記法
            r'@([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
            
            # 自然言語パターン（日本語）
            r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)(?:を|の|ファイル|file)',
            r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)(?:を読み込んで|を確認して|を見て|を分析して)',
            r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)(?:の内容|の中身)',
            
            # 自然言語パターン（英語）
            r'(?:read|check|analyze|look at|examine)\s+([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
            r'(?:file|content of|contents of)\s+([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)',
            r'([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+)\s+(?:file|content)',
        ]
        
        # フォルダ参照パターン
        self.folder_patterns = [
            # 自然言語パターン（日本語）
            r'([a-zA-Z0-9_\-./\\]+/)(?:フォルダ|ディレクトリ|の中|内のファイル)',
            r'([a-zA-Z0-9_\-./\\]+)(?:フォルダ内|ディレクトリ内|の全ファイル)',
            
            # 自然言語パターン（英語）
            r'(?:in|inside|from)\s+([a-zA-Z0-9_\-./\\]+/)(?:folder|directory)',
            r'(?:all files in|files from)\s+([a-zA-Z0-9_\-./\\]+/?)',
            r'([a-zA-Z0-9_\-./\\]+/)(?:folder|directory)',
        ]
        
        # ファイル拡張子パターン
        self.extension_patterns = [
            r'(?:全ての|すべての|all)\s*([a-zA-Z0-9]+)\s*(?:ファイル|files)',
            r'(?:.*\.([a-zA-Z0-9]+))\s*(?:ファイル|files)',
        ]
    
    def parse_query(self, query: str) -> Dict[str, List[str]]:
        """クエリからファイル参照を解析"""
        result = {
            'files': [],
            'folders': [],
            'extensions': [],
            'processed_query': query
        }
        
        # @記法とファイル参照の解析
        files = self._extract_file_references(query)
        result['files'] = files
        
        # フォルダ参照の解析
        folders = self._extract_folder_references(query)
        result['folders'] = folders
        
        # 拡張子パターンの解析
        extensions = self._extract_extension_patterns(query)
        result['extensions'] = extensions
        
        # 処理済みクエリ（ファイル参照を除去）
        result['processed_query'] = self._clean_query(query, files, folders)
        
        return result
    
    def _extract_file_references(self, query: str) -> List[str]:
        """ファイル参照を抽出"""
        files = []
        
        for pattern in self.file_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # パスの正規化
                file_path = self._normalize_path(match)
                if file_path and file_path not in files:
                    files.append(file_path)
        
        return files
    
    def _extract_folder_references(self, query: str) -> List[str]:
        """フォルダ参照を抽出"""
        folders = []
        
        for pattern in self.folder_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                # パスの正規化
                folder_path = self._normalize_path(match)
                if folder_path and folder_path not in folders:
                    # フォルダパスは/で終わるように
                    if not folder_path.endswith('/'):
                        folder_path += '/'
                    folders.append(folder_path)
        
        return folders
    
    def _extract_extension_patterns(self, query: str) -> List[str]:
        """拡張子パターンを抽出"""
        extensions = []
        
        for pattern in self.extension_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                
                if match and match not in extensions:
                    extensions.append(match.lower())
        
        return extensions
    
    def _normalize_path(self, path: str) -> Optional[str]:
        """パスを正規化"""
        if not path:
            return None
        
        # @記法の場合は@を削除
        if path.startswith('@'):
            path = path[1:]
        
        # 空文字や無効なパスをフィルタ
        if not path or len(path) < 2:
            return None
        
        # バックスラッシュをスラッシュに統一
        path = path.replace('\\', '/')
        
        return path
    
    def _clean_query(self, query: str, files: List[str], folders: List[str]) -> str:
        """クエリからファイル参照を除去して処理済みクエリを作成"""
        cleaned = query
        
        # @記法を削除
        cleaned = re.sub(r'@[a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+', '', cleaned)
        
        # ファイル名と関連語句を削除
        for file in files:
            # ファイル名自体を削除
            cleaned = re.sub(re.escape(file), '', cleaned, flags=re.IGNORECASE)
            
            # ファイル名 + 関連語句を削除
            patterns_to_remove = [
                rf'{re.escape(file)}(?:を|の|ファイル|file)',
                rf'{re.escape(file)}(?:を読み込んで|を確認して|を見て|を分析して)',
                rf'{re.escape(file)}(?:の内容|の中身)',
                rf'(?:read|check|analyze|look at|examine)\s+{re.escape(file)}',
                rf'(?:file|content of|contents of)\s+{re.escape(file)}',
                rf'{re.escape(file)}\s+(?:file|content)',
            ]
            
            for pattern in patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # フォルダ参照を削除
        for folder in folders:
            folder_clean = folder.rstrip('/')
            patterns_to_remove = [
                rf'{re.escape(folder_clean)}(?:フォルダ|ディレクトリ|の中|内のファイル)',
                rf'{re.escape(folder_clean)}(?:フォルダ内|ディレクトリ内|の全ファイル)',
                rf'(?:in|inside|from)\s+{re.escape(folder)}(?:folder|directory)',
                rf'(?:all files in|files from)\s+{re.escape(folder_clean)}',
                rf'{re.escape(folder)}(?:folder|directory)',
            ]
            
            for pattern in patterns_to_remove:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # 余分な空白を削除
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def find_files_by_extension(self, extension: str, directory: str = '.') -> List[str]:
        """指定拡張子のファイルを検索"""
        try:
            search_path = self.root_path / directory
            if not search_path.exists():
                return []
            
            pattern = f"*.{extension}"
            files = []
            
            for file_path in search_path.rglob(pattern):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.root_path)
                    files.append(str(relative_path))
            
            return files
        except Exception:
            return []
    
    def find_files_in_folder(self, folder: str) -> List[str]:
        """指定フォルダ内のファイルを検索"""
        try:
            folder_path = self.root_path / folder.rstrip('/')
            if not folder_path.exists() or not folder_path.is_dir():
                return []
            
            files = []
            for file_path in folder_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.root_path)
                    files.append(str(relative_path))
            
            return files
        except Exception:
            return []
    
    def resolve_file_path(self, file_ref: str) -> Optional[Path]:
        """ファイル参照を実際のパスに解決"""
        try:
            file_path = self.root_path / file_ref
            if file_path.exists() and file_path.is_file():
                return file_path
            
            # ファイルが存在しない場合、類似ファイルを検索
            return self._find_similar_file(file_ref)
        except Exception:
            return None
    
    def _find_similar_file(self, file_ref: str) -> Optional[Path]:
        """類似ファイルを検索"""
        try:
            file_name = Path(file_ref).name
            
            # プロジェクト内で同名ファイルを検索
            for file_path in self.root_path.rglob(file_name):
                if file_path.is_file():
                    return file_path
            
            return None
        except Exception:
            return None