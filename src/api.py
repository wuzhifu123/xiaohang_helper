import requests
from typing import Optional, Dict, Any
from config import API_URL, HEADERS, MODEL_NAME, REQUEST_TIMEOUT


def call_api(system_prompt: str, messages: list) -> Optional[str]:
    """调用硅基流动 API 获取 AI 回答"""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
        }
        
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 401:
            return None, "API Key 失效，请重新配置"
        elif response.status_code != 200:
            return None, f"API 异常，状态码：{response.status_code}"
        
        result = response.json()
        
        try:
            answer = result["choices"][0]["message"]["content"]
            return answer, None
        except (KeyError, IndexError):
            return None, "AI 返回格式异常，请重试"
            
    except requests.exceptions.Timeout:
        return None, "AI 响应超时，请稍后再试"
    except requests.exceptions.ConnectionError:
        return None, "网络连接失败，请检查网络"
    except Exception as e:
        return None, f"发生错误：{e}"