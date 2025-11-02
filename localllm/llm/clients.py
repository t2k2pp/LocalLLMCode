"""LLM client implementations"""

import json
import asyncio
import aiohttp
from typing import Dict, Any

try:
    from rich.console import Console
    console = Console()
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
    console = Console()

class LLMClient:
    """革新的なLLMクライアント - 複数プロバイダー対応"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.provider = config.get('provider', 'lmstudio')
        self.connection_retries = 0
        self.max_retries = 3
        self.health_check_enabled = True
        self.last_health_check = 0
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate(self, prompt: str, system_prompt: str = "", 
                      stream: bool = True) -> str:
        """LLMから応答を生成"""
        import time
        
        # ヘルスチェック（5分間隔）
        if self.health_check_enabled and time.time() - self.last_health_check > 300:
            health_ok = await self._health_check()
            if not health_ok and self.connection_retries < self.max_retries:
                await self._attempt_reconnection()
            self.last_health_check = time.time()
        
        provider = self.config.get('provider', 'lmstudio')
        
        try:
            if provider == 'lmstudio':
                result = await self._generate_lmstudio(prompt, system_prompt, stream)
            elif provider == 'azure':
                result = await self._generate_azure(prompt, system_prompt, stream)
            elif provider == 'gemini':
                result = await self._generate_gemini(prompt, system_prompt, stream)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            # 成功時はリトライカウンターをリセット
            self.connection_retries = 0
            return result
            
        except Exception as e:
            console.print(f"[red]Connection error: {e}[/red]")
            
            # 自動再接続を試行
            if self.connection_retries < self.max_retries:
                console.print(f"[yellow]Attempting reconnection ({self.connection_retries + 1}/{self.max_retries})...[/yellow]")
                if await self._attempt_reconnection():
                    # 再接続成功後、再度試行
                    return await self.generate(prompt, system_prompt, stream)
            
            # 最大試行回数に達した場合のフォールバック
            return f"Connection failed after {self.max_retries} attempts. Please check your {provider} configuration and connection."
    
    async def _generate_lmstudio(self, prompt: str, system_prompt: str, 
                                stream: bool) -> str:
        """LM Studio API呼び出し"""
        url = f"{self.config.get('server_url', 'http://localhost:1234')}/v1/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.get('model', 'default'),
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        try:
            if stream:
                return await self._stream_response(url, payload)
            else:
                timeout = aiohttp.ClientTimeout(total=60)
                async with self.session.post(url, json=payload, timeout=timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
        except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
            console.print(f"[red]Error connecting to LM Studio: {e}[/red]")
            return "I apologize, but I'm having trouble connecting to the local LLM. Please check if LM Studio is running."
        except Exception as e:
            console.print(f"[red]Unexpected LM Studio error: {e}[/red]")
            return f"LM Studio error: {str(e)}"
    
    async def _stream_response(self, url: str, payload: Dict) -> str:
        """ストリーミングレスポンスを処理"""
        full_response = ""
        
        try:
            timeout = aiohttp.ClientTimeout(total=120, sock_read=30)  # タイムアウト設定
            async with self.session.post(url, json=payload, timeout=timeout) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text}")
                
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            delta = data.get('choices', [{}])[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response += content
                                print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            continue
                        except Exception as parse_error:
                            console.print(f"[yellow]Stream parse error: {parse_error}[/yellow]")
                            continue
            
            print()  # 改行
            return full_response
            
        except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
            console.print(f"[red]Streaming connection error: {e}[/red]")
            # 接続エラー時はシンプルなレスポンスで代替
            return "Connection error occurred during streaming response. Please check LM Studio connection."
        except Exception as e:
            console.print(f"[red]Unexpected streaming error: {e}[/red]")
            return f"Streaming error: {str(e)}"
    
    async def _generate_azure(self, prompt: str, system_prompt: str, 
                             stream: bool) -> str:
        """Azure ChatGPT API呼び出し"""
        azure_config = self.config.get('azure', {})
        
        api_key = azure_config.get('api_key')
        endpoint = azure_config.get('endpoint')
        deployment_name = azure_config.get('deployment_name')
        api_version = azure_config.get('api_version', '2024-02-15-preview')
        
        if not all([api_key, endpoint, deployment_name]):
            return "Azure API configuration missing. Please set api_key, endpoint, and deployment_name in [azure] section."
        
        url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
        
        headers = {
            'Content-Type': 'application/json',
            'api-key': api_key
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": stream
        }
        
        try:
            if stream:
                return await self._stream_azure_response(url, headers, payload)
            else:
                async with self.session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return f"Azure API error ({resp.status}): {error_text}"
                    
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
        except Exception as e:
            console.print(f"[red]Error connecting to Azure API: {e}[/red]")
            return "I apologize, but I'm having trouble connecting to Azure ChatGPT. Please check your configuration."
    
    async def _stream_azure_response(self, url: str, headers: dict, payload: dict) -> str:
        """Azure APIストリーミングレスポンスを処理"""
        full_response = ""
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                return f"Azure API error ({resp.status}): {error_text}"
            
            async for line in resp.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data_str = line[6:]
                    if data_str == '[DONE]':
                        break
                    
                    try:
                        data = json.loads(data_str)
                        choices = data.get('choices', [])
                        if choices:
                            delta = choices[0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                full_response += content
                                print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        
        print()  # 改行
        return full_response
    
    async def _generate_gemini(self, prompt: str, system_prompt: str, 
                              stream: bool) -> str:
        """Gemini API呼び出し"""
        gemini_config = self.config.get('gemini', {})
        
        api_key = gemini_config.get('api_key')
        model = gemini_config.get('model', 'gemini-pro')
        
        if not api_key:
            return "Gemini API configuration missing. Please set api_key in [gemini] section."
        
        # Gemini APIは現在ストリーミングをサポートしていない
        if stream:
            console.print("[yellow]Note: Gemini API doesn't support streaming, using non-streaming mode[/yellow]")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        # Geminiは異なる形式でメッセージを送信
        content_parts = []
        
        if system_prompt:
            content_parts.append({"text": f"System: {system_prompt}\n\nUser: {prompt}"})
        else:
            content_parts.append({"text": prompt})
        
        payload = {
            "contents": [{
                "parts": content_parts
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
                "topP": 0.8,
                "topK": 10
            }
        }
        
        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    return f"Gemini API error ({resp.status}): {error_text}"
                
                data = await resp.json()
                
                # Geminiのレスポンス形式から回答を抽出
                candidates = data.get('candidates', [])
                if not candidates:
                    return "No response from Gemini API"
                
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if not parts:
                    return "Empty response from Gemini API"
                
                response_text = parts[0].get('text', '')
                
                # ストリーミング風に出力（実際はストリーミングではない）
                if stream:
                    for char in response_text:
                        print(char, end='', flush=True)
                        await asyncio.sleep(0.01)  # 小さな遅延でストリーミング風に
                    print()  # 改行
                
                return response_text
                
        except Exception as e:
            console.print(f"[red]Error connecting to Gemini API: {e}[/red]")
            return "I apologize, but I'm having trouble connecting to Gemini API. Please check your configuration."
    
    async def _health_check(self) -> bool:
        """ヘルスチェックを実行"""
        try:
            provider = self.config.get('provider', 'lmstudio')
            
            if provider == 'lmstudio':
                url = f"{self.config.get('server_url', 'http://localhost:1234')}/v1/models"
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
            elif provider == 'azure':
                # Azure の場合は簡単なAPIコールでテスト
                azure_config = self.config.get('azure', {})
                if not azure_config.get('api_key'):
                    return False
                return True  # 設定があれば健全とみなす
            elif provider == 'gemini':
                # Gemini の場合は設定をチェック
                gemini_config = self.config.get('gemini', {})
                return bool(gemini_config.get('api_key'))
            
            return False
        except:
            return False
    
    async def _attempt_reconnection(self) -> bool:
        """再接続を試行"""
        try:
            self.connection_retries += 1
            console.print(f"[yellow]Attempting reconnection {self.connection_retries}/{self.max_retries}...[/yellow]")
            
            # セッションを完全にクリーンアップ
            if self.session and not self.session.closed:
                try:
                    await asyncio.wait_for(self.session.close(), timeout=5.0)
                except asyncio.TimeoutError:
                    console.print("[yellow]Session close timeout - forcing cleanup[/yellow]")
                except Exception as cleanup_error:
                    console.print(f"[yellow]Session cleanup error: {cleanup_error}[/yellow]")
            
            # 待機時間を増やす
            await asyncio.sleep(3 + self.connection_retries)  # 待機時間を徐々に増加
            
            # 新しいセッションを作成
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(connector=connector)
            
            # ヘルスチェックで確認
            health_ok = await self._health_check()
            if health_ok:
                console.print("[green]Reconnection successful![/green]")
                return True
            else:
                console.print("[red]Reconnection failed - service not responding[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]Reconnection error: {e}[/red]")
            return False