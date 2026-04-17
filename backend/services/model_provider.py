"""
模型提供商服务层
统一管理所有 AI 模型提供商的 API 调用
"""
import json
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, field


@dataclass
class ModelProviderConfig:
    """模型提供商配置"""
    name: str
    api_key: str = ""
    base_url: str = ""
    default_model: str = ""
    supports_streaming: bool = True
    api_version: str = ""
    extra_headers: Dict[str, str] = field(default_factory=dict)
    extra_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str


@dataclass
class ChatResponse:
    """聊天响应"""
    content: str
    total_tokens: int = 0
    finished: bool = True


class BaseModelProvider(ABC):
    """模型提供商基类"""

    def __init__(self, config: ModelProviderConfig):
        self.config = config

    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        """发送聊天请求，返回流式响应"""
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        """列出可用模型"""
        pass

    @abstractmethod
    async def test_connection(self) -> tuple[bool, str]:
        """测试连接，返回 (成功, 消息)"""
        pass

    def _build_headers(self) -> Dict[str, str]:
        """构建请求头"""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        for k, v in self.config.extra_headers.items():
            headers[k] = v
        return headers


class OllamaProvider(BaseModelProvider):
    """Ollama 本地模型提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/api/chat"
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.config.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass
        return [self.config.default_model]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.config.base_url}/api/tags")
                if resp.status_code == 200:
                    return True, "连接成功"
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class OpenAIProvider(BaseModelProvider):
    """OpenAI API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "gpt-3.5-turbo",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.config.base_url}/models",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            pass
        return ["gpt-3.5-turbo", "gpt-4"]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.config.base_url}/models", headers=headers)
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class DeepSeekProvider(BaseModelProvider):
    """DeepSeek API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "deepseek-chat",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return ["deepseek-chat", "deepseek-coder"]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                elif resp.status_code == 403:
                    return False, "API Key 权限不足"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class AnthropicProvider(BaseModelProvider):
    """Anthropic Claude API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/messages"
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": self.config.api_version or "2023-06-01",
            "content-type": "application/json",
        }
        system = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model or "claude-3-5-haiku-20241022",
            "max_tokens": max_tokens,
            "messages": chat_messages,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if temperature != 0.7:
            payload["temperature"] = temperature

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            delta = data.get("delta", {})
                            if delta.get("type") == "content_block_delta":
                                content = delta.get("text", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": self.config.api_version or "2023-06-01",
                "content-type": "application/json",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/messages",
                    headers=headers,
                    json={"model": "claude-3-5-haiku-20241022", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class AzureOpenAIProvider(BaseModelProvider):
    """Azure OpenAI Service 提供商"""

    def __init__(self, config: ModelProviderConfig):
        super().__init__(config)
        self.deployment_name = config.extra_config.get("deployment_name", "")

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        deployment = self.deployment_name or model
        url = f"{self.config.base_url}/openai/deployments/{deployment}/chat/completions?api-version={self.config.api_version}"
        headers = {
            "Content-Type": "application/json",
            "api-key": self.config.api_key,
        }
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return ["gpt-4", "gpt-4-turbo", "gpt-35-turbo"]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            deployment = self.deployment_name or "gpt-4"
            headers = {"api-key": self.config.api_key}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/openai/deployments/{deployment}/chat/completions?api-version={self.config.api_version}",
                    headers=headers,
                    json={"messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                elif resp.status_code == 404:
                    return False, f"部署 '{deployment}' 不存在"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class OpenRouterProvider(BaseModelProvider):
    """OpenRouter 聚合 API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        headers["HTTP-Referer"] = "https://astral-lounge.local"
        headers["X-Title"] = "AstralLounge"
        payload = {
            "model": model or "openai/gpt-3.5-turbo",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        try:
            headers = self._build_headers()
            headers["HTTP-Referer"] = "https://astral-lounge.local"
            headers["X-Title"] = "AstralLounge"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            pass
        return ["openai/gpt-3.5-turbo", "openai/gpt-4", "anthropic/claude-3-haiku"]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            headers["HTTP-Referer"] = "https://astral-lounge.local"
            headers["X-Title"] = "AstralLounge"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class GroqProvider(BaseModelProvider):
    """Groq 免费 API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "llama-3.1-8b-instant",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "llama-3.1-405b-reasoning",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class TogetherProvider(BaseModelProvider):
    """Together AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "meta-llama/Llama-3-8B-Instruct-Turbo",
            "meta-llama/Llama-3-70B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "Qwen/Qwen2-72B-Instruct",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": self.config.default_model or "meta-llama/Llama-3-8B-Instruct-Turbo", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class FireworksProvider(BaseModelProvider):
    """Fireworks AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "accounts/fireworks/models/llama-v3-8b-instruct",
            "accounts/fireworks/models/llama-v3-70b-instruct",
            "accounts/fireworks/models/mixtral-8x22b-instruct",
            "accounts/fireworks/models/qwen2-72b-instruct",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": self.config.default_model or "accounts/fireworks/models/llama-v3-8b-instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class NovitaProvider(BaseModelProvider):
    """Novita AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "meta-llama/llama-3.1-8b-instruct",
            "meta-llama/llama-3.1-70b-instruct",
            "mistralai/mistral-7b-instruct",
            "qwen/qwen2-72b-instruct",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": self.config.default_model or "meta-llama/llama-3.1-8b-instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class SiliconFlowProvider(BaseModelProvider):
    """SiliconFlow 硅基流动 API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "Qwen/Qwen2.5-7B-Instruct",
            "Qwen/Qwen2.5-14B-Instruct",
            "deepseek-ai/DeepSeek-V2.5",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "THUDM/glm-4-9b-chat",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": self.config.default_model or "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class CustomOpenAIProvider(BaseModelProvider):
    """兼容 OpenAI 格式的自定义 API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [self.config.default_model]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": self.config.default_model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class LLMStudioProvider(BaseModelProvider):
    """LM Studio 本地模型提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/v1/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [self.config.default_model]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.config.base_url}/v1/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return True, f"连接成功，当前加载模型: {len(data.get('data', []))}"
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class KoboldCPPProvider(BaseModelProvider):
    """KoboldCpp 本地模型提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/v1/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or self.config.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_output": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [self.config.default_model]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.config.base_url}/v1/model", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    name = data.get("result", "unknown")
                    return True, f"连接成功，当前模型: {name}"
                return False, f"HTTP {resp.status_code}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class MistralProvider(BaseModelProvider):
    """Mistral AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "mistral-small-latest",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "mistral-small-latest",
            "mistral-medium-latest",
            "mistral-large-latest",
            "mistral-nemo",
            "mistral-7b-instruct",
            "mixtral-8x7b-instruct",
            "mixtral-8x22b-instruct",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "mistral-small-latest", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class GoogleGeminiProvider(BaseModelProvider):
    """Google Gemini API 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/models/{model or 'gemini-1.5-flash'}:streamGenerateContent"
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"

        chat_messages = []
        for m in messages:
            if m.role == "user":
                chat_messages.append({"role": "user", "parts": [{"text": m.content}]})
            elif m.role == "model":
                chat_messages.append({"role": "model", "parts": [{"text": m.content}]})
            elif m.role == "system":
                pass

        payload = {
            "contents": chat_messages,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            candidates = data.get("candidates", [])
                            if candidates:
                                content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
            "gemini-pro",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            headers["Content-Type"] = "application/json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/models/gemini-1.5-flash:generateContent",
                    headers=headers,
                    json={"contents": [{"role": "user", "parts": [{"text": "hi"}]}], "generationConfig": {"maxOutputTokens": 5}}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class CohereProvider(BaseModelProvider):
    """Cohere AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat"
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"

        chat_messages = []
        for m in messages:
            if m.role != "system":
                chat_messages.append({"role": m.role, "message": m.content})

        payload = {
            "model": model or "command-r-plus",
            "message": messages[-1].content if messages else "",
            "chat_history": [{"role": m.role, "content": m.content} for m in messages[:-1] if m.role != "system"],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("text", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "command-r-plus",
            "command-r",
            "command",
            "command-light",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            headers["Content-Type"] = "application/json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat",
                    headers=headers,
                    json={"model": "command-r-plus", "message": "hi", "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class AI21Provider(BaseModelProvider):
    """AI21 Jurassic AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "j2-ultra",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "j2-ultra",
            "j2-mid",
            "j2-light",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "j2-ultra", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class PerplexityProvider(BaseModelProvider):
    """Perplexity AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "llama-3.1-sonar-large-128k-online",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "llama-3.1-sonar-large-128k-online", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class XAIProvider(BaseModelProvider):
    """xAI Grok AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "grok-2-1212",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "grok-2-1212",
            "grok-2-v1212",
            "grok-1",
            "grok-1.5",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "grok-2-1212", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class TencentCloudProvider(BaseModelProvider):
    """腾讯云混元 AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/hunyuan continuation/chatpro"
        headers = self._build_headers()
        headers["Content-Type"] = "application/json"

        chat_messages = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]

        payload = {
            "Model": model or "hunyuan-pro",
            "Messages": chat_messages,
            "Temperature": temperature,
            "TopP": kwargs.get("top_p", 0.9),
            "MaxTokens": max_tokens,
            "Stream": stream,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            choices = data.get("Choices", [{}])
                            if choices:
                                content = choices[0].get("Delta", {}).get("content", "") or choices[0].get("Message", {}).get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "hunyuan-pro",
            "hunyuan-standard",
            "hunyuan-lite",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            headers["Content-Type"] = "application/json"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/hunyuan continuation/chatpro",
                    headers=headers,
                    json={"Model": "hunyuan-pro", "Messages": [{"role": "user", "content": "hi"}], "MaxTokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class BaichuanProvider(BaseModelProvider):
    """百川 AI 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/v1/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "baichuan4",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "baichuan4",
            "baichuan3-turbo",
            "baichuan3-turbo-128k",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    headers=headers,
                    json={"model": "baichuan4", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class ZhipuProvider(BaseModelProvider):
    """智谱 AI GLM 提供商"""

    async def chat(
        self,
        messages: List[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = True,
        **kwargs
    ) -> AsyncIterator[str]:
        url = f"{self.config.base_url}/chat/completions"
        headers = self._build_headers()
        payload = {
            "model": model or "glm-4",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": stream,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[5:])
                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        return [
            "glm-4",
            "glm-4-plus",
            "glm-4-air",
            "glm-4-flashx",
            "glm-4-airx",
            "glm-3-turbo",
        ]

    async def test_connection(self) -> tuple[bool, str]:
        try:
            headers = self._build_headers()
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json={"model": "glm-4", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
                )
                if resp.status_code == 200:
                    return True, "连接成功"
                elif resp.status_code == 401:
                    return False, "API Key 无效"
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, f"连接失败: {str(e)}"


class ModelProviderRegistry:
    """模型提供商注册表"""

    _instance = None
    _providers: Dict[str, type] = {}
    _configs: Dict[str, ModelProviderConfig] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._register_default_providers()
        return cls._instance

    def _register_default_providers(self):
        """注册默认提供商"""
        self._providers = {
            "ollama": OllamaProvider,
            "openai": OpenAIProvider,
            "deepseek": DeepSeekProvider,
            "anthropic": AnthropicProvider,
            "azure": AzureOpenAIProvider,
            "openrouter": OpenRouterProvider,
            "groq": GroqProvider,
            "together": TogetherProvider,
            "fireworks": FireworksProvider,
            "novita": NovitaProvider,
            "siliconflow": SiliconFlowProvider,
            "lmstudio": LLMStudioProvider,
            "koboldcpp": KoboldCPPProvider,
            "custom": CustomOpenAIProvider,
            "mistral": MistralProvider,
            "gemini": GoogleGeminiProvider,
            "cohere": CohereProvider,
            "ai21": AI21Provider,
            "perplexity": PerplexityProvider,
            "xai": XAIProvider,
            "tencent": TencentCloudProvider,
            "baichuan": BaichuanProvider,
            "zhipu": ZhipuProvider,
        }

    def register_provider(self, name: str, provider_class: type, config: ModelProviderConfig):
        """注册自定义提供商"""
        self._providers[name] = provider_class
        self._configs[name] = config

    def update_config(self, name: str, config: ModelProviderConfig):
        """更新提供商配置"""
        self._configs[name] = config

    def get_config(self, name: str) -> Optional[ModelProviderConfig]:
        """获取提供商配置"""
        return self._configs.get(name)

    def get_provider(self, name: str) -> Optional[BaseModelProvider]:
        """获取提供商实例"""
        provider_class = self._providers.get(name)
        if not provider_class:
            return None
        config = self._configs.get(name)
        if not config:
            return None
        return provider_class(config)

    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有可用提供商"""
        result = []
        for name in self._providers:
            config = self._configs.get(name)
            result.append({
                "id": name,
                "name": name,
                "has_api_key": bool(config and config.api_key),
                "base_url": config.base_url if config else "",
                "default_model": config.default_model if config else "",
            })
        return result

    def setup_from_settings(self, settings):
        """从设置初始化所有提供商配置"""
        self._configs = {
            "ollama": ModelProviderConfig(
                name="ollama",
                base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"),
                default_model=getattr(settings, "default_model_name", "llama3.2"),
                supports_streaming=True,
            ),
            "openai": ModelProviderConfig(
                name="openai",
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url or "https://api.openai.com/v1",
                default_model="gpt-3.5-turbo",
                supports_streaming=True,
            ),
            "deepseek": ModelProviderConfig(
                name="deepseek",
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1",
                default_model="deepseek-chat",
                supports_streaming=True,
            ),
            "anthropic": ModelProviderConfig(
                name="anthropic",
                api_key=settings.claude_api_key,
                base_url=settings.claude_base_url or "https://api.anthropic.com/v1",
                default_model="claude-3-5-haiku-20241022",
                supports_streaming=True,
                api_version=settings.anthropic_api_version or "2023-06-01",
            ),
            "azure": ModelProviderConfig(
                name="azure",
                api_key=settings.azure_api_key,
                base_url=settings.azure_endpoint,
                default_model="gpt-4",
                supports_streaming=True,
                api_version=settings.azure_api_version or "2024-02-01",
                extra_config={"deployment_name": getattr(settings, "azure_deployment", "")},
            ),
            "openrouter": ModelProviderConfig(
                name="openrouter",
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_model="openai/gpt-3.5-turbo",
                supports_streaming=True,
            ),
            "groq": ModelProviderConfig(
                name="groq",
                api_key=getattr(settings, "groq_api_key", ""),
                base_url="https://api.groq.com/openai/v1",
                default_model="llama-3.1-8b-instant",
                supports_streaming=True,
            ),
            "together": ModelProviderConfig(
                name="together",
                api_key=getattr(settings, "together_api_key", ""),
                base_url="https://api.together.xyz/v1",
                default_model="meta-llama/Llama-3-8B-Instruct-Turbo",
                supports_streaming=True,
            ),
            "fireworks": ModelProviderConfig(
                name="fireworks",
                api_key=getattr(settings, "fireworks_api_key", ""),
                base_url="https://api.fireworks.ai/inference/v1",
                default_model="accounts/fireworks/models/llama-v3-8b-instruct",
                supports_streaming=True,
            ),
            "novita": ModelProviderConfig(
                name="novita",
                api_key=getattr(settings, "novita_api_key", ""),
                base_url="https://api.novita.ai/v3",
                default_model="meta-llama/llama-3.1-8b-instruct",
                supports_streaming=True,
            ),
            "siliconflow": ModelProviderConfig(
                name="siliconflow",
                api_key=getattr(settings, "siliconflow_api_key", ""),
                base_url="https://api.siliconflow.cn/v1",
                default_model="Qwen/Qwen2.5-7B-Instruct",
                supports_streaming=True,
            ),
            "lmstudio": ModelProviderConfig(
                name="lmstudio",
                api_key="",
                base_url=getattr(settings, "lmstudio_base_url", "http://localhost:1234"),
                default_model=getattr(settings, "lmstudio_model", "local-model"),
                supports_streaming=True,
            ),
            "koboldcpp": ModelProviderConfig(
                name="koboldcpp",
                api_key="",
                base_url=getattr(settings, "koboldcpp_base_url", "http://localhost:5000"),
                default_model=getattr(settings, "koboldcpp_model", "local-model"),
                supports_streaming=True,
            ),
            "custom": ModelProviderConfig(
                name="custom",
                api_key="",
                base_url="",
                default_model="",
                supports_streaming=True,
            ),
            "mistral": ModelProviderConfig(
                name="mistral",
                api_key=getattr(settings, "mistral_api_key", ""),
                base_url="https://api.mistral.ai/v1",
                default_model="mistral-small-latest",
                supports_streaming=True,
            ),
            "gemini": ModelProviderConfig(
                name="gemini",
                api_key=getattr(settings, "gemini_api_key", ""),
                base_url="https://generativelanguage.googleapis.com/v1beta",
                default_model="gemini-1.5-flash",
                supports_streaming=True,
            ),
            "cohere": ModelProviderConfig(
                name="cohere",
                api_key=getattr(settings, "cohere_api_key", ""),
                base_url="https://api.cohere.ai/v1",
                default_model="command-r-plus",
                supports_streaming=True,
            ),
            "ai21": ModelProviderConfig(
                name="ai21",
                api_key=getattr(settings, "ai21_api_key", ""),
                base_url="https://api.ai21.com/studio/v1",
                default_model="j2-ultra",
                supports_streaming=True,
            ),
            "perplexity": ModelProviderConfig(
                name="perplexity",
                api_key=getattr(settings, "perplexity_api_key", ""),
                base_url="https://api.perplexity.ai",
                default_model="llama-3.1-sonar-large-128k-online",
                supports_streaming=True,
            ),
            "xai": ModelProviderConfig(
                name="xai",
                api_key=getattr(settings, "xai_api_key", ""),
                base_url="https://api.x.ai/v1",
                default_model="grok-2-1212",
                supports_streaming=True,
            ),
            "tencent": ModelProviderConfig(
                name="tencent",
                api_key=getattr(settings, "tencent_secret_id", ""),
                base_url="https://hunyuan.cloud.tencent.com",
                default_model="hunyuan-pro",
                supports_streaming=True,
            ),
            "baichuan": ModelProviderConfig(
                name="baichuan",
                api_key=getattr(settings, "baichuan_api_key", ""),
                base_url="https://api.baichuan-ai.com/v1",
                default_model="baichuan4",
                supports_streaming=True,
            ),
            "zhipu": ModelProviderConfig(
                name="zhipu",
                api_key=getattr(settings, "zhipu_api_key", ""),
                base_url="https://open.bigmodel.cn/api/paas/v4",
                default_model="glm-4",
                supports_streaming=True,
            ),
        }

    async def get_provider_models(self, name: str) -> List[str]:
        """获取指定提供商的模型列表"""
        provider = self.get_provider(name)
        if not provider:
            return []
        try:
            return await provider.list_models()
        except Exception:
            return []

    async def test_provider(self, name: str) -> tuple[bool, str]:
        """测试指定提供商的连接"""
        provider = self.get_provider(name)
        if not provider:
            return False, "提供商不存在"
        try:
            return await provider.test_connection()
        except Exception as e:
            return False, f"测试失败: {str(e)}"


_provider_registry: Optional[ModelProviderRegistry] = None


def get_provider_registry() -> ModelProviderRegistry:
    """获取提供商注册表单例"""
    global _provider_registry
    if _provider_registry is None:
        _provider_registry = ModelProviderRegistry()
    return _provider_registry


async def chat_with_provider(
    provider_name: str,
    messages: List[ChatMessage],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    stream: bool = True,
) -> AsyncIterator[str]:
    """通过指定提供商发送聊天请求"""
    registry = get_provider_registry()
    provider = registry.get_provider(provider_name)
    if not provider:
        yield f"错误: 未知的提供商 '{provider_name}'"
        return
    async for chunk in provider.chat(messages, model, temperature, max_tokens, stream):
        yield chunk
