"""
Client per l'integrazione con OpenRouter
"""

import requests
import json
from typing import List, Dict, Optional


class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://analisi-mu.ai4educ.org",
            "X-Title": "Analisi MU - AI Annotation System"
        }
    
    def test_connection(self) -> bool:
        """Testa la validità dell'API key"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/key",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> List[Dict]:
        """Recupera la lista dei modelli disponibili"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            print(f"Errore nel recupero modelli OpenRouter: {e}")
            return []
    
    def get_free_models(self) -> List[Dict]:
        """Recupera solo i modelli gratuiti"""
        models = self.get_models()
        free_models = []
        
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '0'))
            completion_price = float(pricing.get('completion', '0'))
            
            if prompt_price == 0 and completion_price == 0:
                free_models.append(model)
        
        return free_models
    
    def get_paid_models(self) -> List[Dict]:
        """Recupera i modelli a pagamento"""
        models = self.get_models()
        paid_models = []
        
        for model in models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '0'))
            completion_price = float(pricing.get('completion', '0'))
            
            if prompt_price > 0 or completion_price > 0:
                paid_models.append(model)
        
        return paid_models
    
    def generate_chat(self, model: str, messages: List[Dict], 
                     temperature: float = 0.7, max_tokens: int = 1000) -> Dict:
        """Genera una risposta usando il modello specificato"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_usage(self) -> Dict:
        """Recupera informazioni sull'utilizzo dell'API"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/key",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


# Modelli gratuiti noti di OpenRouter (aggiornata periodicamente)
KNOWN_FREE_MODELS = [
    {
        "id": "microsoft/phi-3-mini-128k-instruct:free",
        "name": "Phi-3 Mini 128K Instruct (Free)",
        "description": "Microsoft's small but capable model with 128K context",
        "context_length": 128000,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "mistralai/mistral-7b-instruct:free", 
        "name": "Mistral 7B Instruct (Free)",
        "description": "Mistral's 7B parameter instruction-tuned model",
        "context_length": 32768,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "huggingfaceh4/zephyr-7b-beta:free",
        "name": "Zephyr 7B Beta (Free)", 
        "description": "A fine-tuned version of Mistral 7B",
        "context_length": 32768,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "openchat/openchat-7b:free",
        "name": "OpenChat 7B (Free)",
        "description": "An open-source language model fine-tuned with C-RLHF",
        "context_length": 8192,
        "pricing": {"prompt": "0", "completion": "0"}
    },
    {
        "id": "google/gemma-7b-it:free",
        "name": "Gemma 7B Instruct (Free)",
        "description": "Google's Gemma 7B instruction-tuned model",
        "context_length": 8192,
        "pricing": {"prompt": "0", "completion": "0"}
    }
]

# Modelli a pagamento popolari
POPULAR_PAID_MODELS = [
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "description": "OpenAI's latest multimodal flagship model",
        "context_length": 128000,
        "pricing": {"prompt": "0.000005", "completion": "0.000015"}
    },
    {
        "id": "openai/gpt-4o-mini",
        "name": "GPT-4o Mini", 
        "description": "OpenAI's affordable small model for fast, lightweight tasks",
        "context_length": 128000,
        "pricing": {"prompt": "0.00000015", "completion": "0.0000006"}
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "description": "Anthropic's most intelligent model",
        "context_length": 200000,
        "pricing": {"prompt": "0.000003", "completion": "0.000015"}
    },
    {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "description": "Anthropic's fastest and most compact model",
        "context_length": 200000,
        "pricing": {"prompt": "0.00000025", "completion": "0.00000125"}
    },
    {
        "id": "google/gemini-pro-1.5",
        "name": "Gemini Pro 1.5",
        "description": "Google's latest Gemini model with 2M context",
        "context_length": 2000000,
        "pricing": {"prompt": "0.0000025", "completion": "0.0000075"}
    }
]
