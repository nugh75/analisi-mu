#!/usr/bin/env python3
"""
Script per sincronizzare i modelli OpenRouter nel database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, OpenRouterModel

def sync_openrouter_models():
    """Sincronizza i modelli OpenRouter nel database"""
    
    # Modelli OpenRouter forniti dall'utente
    openrouter_models = [
        {
            'model_id': 'reka/flash-3',
            'name': 'Reka: Flash 3 (free)',
            'description': 'Reka Flash 3 is a general-purpose, instruction-tuned large language model with 21 billion parameters, developed by Reka. It excels at general chat, coding tasks, instruction-following, and function calling. Featuring a 32K context length and optimized through reinforcement learning (RLOO), it provides competitive performance comparable to proprietary models within a smaller parameter footprint.',
            'context_length': 33000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '20.9M tokens'
        },
        {
            'model_id': 'moonshot/kimi-vl-a3b-thinking',
            'name': 'Moonshot AI: Kimi VL A3B Thinking (free)',
            'description': 'Kimi-VL is a lightweight Mixture-of-Experts vision-language model that activates only 2.8B parameters per step while delivering strong performance on multimodal reasoning and long-context tasks. The Kimi-VL-A3B-Thinking variant, fine-tuned with chain-of-thought and reinforcement learning, excels in math and visual reasoning benchmarks.',
            'context_length': 131000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '12.8M tokens'
        },
        {
            'model_id': 'google/gemma-3-4b',
            'name': 'Google: Gemma 3 4B (free)',
            'description': 'Gemma 3 introduces multimodality, supporting vision-language input and text outputs. It handles context windows up to 128k tokens, understands over 140 languages, and offers improved math, reasoning, and chat capabilities, including structured outputs and function calling.',
            'context_length': 33000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '11.3M tokens'
        },
        {
            'model_id': 'sarvam/sarvam-m',
            'name': 'Sarvam AI: Sarvam-M (free)',
            'description': 'Sarvam-M is a 24 B-parameter, instruction-tuned derivative of Mistral-Small-3.1-24B-Base-2503, post-trained on English plus eleven major Indic languages. The model introduces a dual-mode interface: "non-think" for low-latency chat and a optional "think" phase that exposes chain-of-thought tokens.',
            'context_length': 33000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '8.91M tokens'
        },
        {
            'model_id': 'featherless/qwerky-72b',
            'name': 'Qwerky 72B (free)',
            'description': 'Qwerky-72B is a linear-attention RWKV variant of the Qwen 2.5 72B model, optimized to significantly reduce computational cost at scale. Leveraging linear attention, it achieves substantial inference speedups (>1000x) while retaining competitive accuracy on common benchmarks.',
            'context_length': 33000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '7.01M tokens'
        },
        {
            'model_id': 'google/gemma-3n-2b',
            'name': 'Google: Gemma 3n 2B (free)',
            'description': 'Gemma 3n E2B IT is a multimodal, instruction-tuned model developed by Google DeepMind, designed to operate efficiently at an effective parameter size of 2B while leveraging a 6B architecture. Based on the MatFormer architecture, it supports nested submodels and modular composition.',
            'context_length': 8000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': '590K tokens'
        },
        {
            'model_id': 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
            'name': 'NVIDIA: Llama 3.1 Nemotron Ultra 253B v1 (free)',
            'description': 'Llama-3.1-Nemotron-Ultra-253B-v1 is a large language model optimized for advanced reasoning, human-interactive chat, retrieval-augmented generation (RAG), and tool-calling tasks. Derived from Meta\'s Llama-3.1-405B-Instruct, it has been significantly customized using Neural Architecture Search (NAS).',
            'context_length': 131000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': 'N/A'
        },
        {
            'model_id': 'deepseek/r1-distill-qwen-14b',
            'name': 'DeepSeek: R1 Distill Qwen 14B (free)',
            'description': 'DeepSeek R1 Distill Qwen 14B is a distilled large language model based on Qwen 2.5 14B, using outputs from DeepSeek R1. It outperforms OpenAI\'s o1-mini across various benchmarks, achieving new state-of-the-art results for dense models.',
            'context_length': 64000,
            'pricing_prompt': 0.0,
            'pricing_completion': 0.0,
            'is_free': True,
            'tokens_used': 'N/A'
        }
    ]
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Sincronizzazione modelli OpenRouter...")
        
        # Rimuovi modelli esistenti
        OpenRouterModel.query.delete()
        
        added_count = 0
        for model_data in openrouter_models:
            try:
                model = OpenRouterModel(
                    model_id=model_data['model_id'],
                    name=model_data['name'],
                    description=model_data['description'],
                    context_length=model_data['context_length'],
                    pricing_prompt=model_data['pricing_prompt'],
                    pricing_completion=model_data['pricing_completion'],
                    is_free=model_data['is_free'],
                    is_available=True
                )
                
                db.session.add(model)
                added_count += 1
                print(f"➕ Aggiunto: {model_data['name']}")
                
            except Exception as e:
                print(f"❌ Errore aggiungendo {model_data['name']}: {e}")
        
        try:
            db.session.commit()
            print(f"✅ Sincronizzazione completata! {added_count} modelli aggiunti.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nel salvataggio: {e}")
            return False
        
        print("\n📊 Modelli OpenRouter disponibili:")
        models = OpenRouterModel.query.all()
        for model in models:
            context = f"{model.context_length//1000}K" if model.context_length else "N/A"
            print(f"  - {model.name} (Context: {context})")
        
        return True

if __name__ == "__main__":
    success = sync_openrouter_models()
    sys.exit(0 if success else 1)
