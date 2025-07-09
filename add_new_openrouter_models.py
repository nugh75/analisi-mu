#!/usr/bin/env python3
"""
Script per aggiungere i nuovi modelli OpenRouter gratuiti del 2025
"""

from app import create_app
from models import db, OpenRouterModel

# Nuovi modelli OpenRouter gratuiti 2025
NEW_FREE_MODELS = [
    {
        'model_id': 'sarvam/sarvam-m',
        'display_name': 'Sarvam AI - Sarvam-M',
        'description': 'Dual "non-think / think", EN + 11 Indic; chat · reasoning · math · coding',
        'context_length': 33000,
        'parameters': '24B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'recursal/qwerky-72b',
        'display_name': 'Qwerky 72B',
        'description': '≈ 30 languages; linear-attention, fast large-context chat',
        'context_length': 33000,
        'parameters': '72B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'google/gemma-3n-2b',
        'display_name': 'Google Gemma 3n 2B',
        'description': 'MatFormer; multimodal, multilingual, reasoning, code',
        'context_length': 32000,
        'parameters': '2B eff. (6B arch)',
        'modality': 'multimodal',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'qwen/qwen-3-4b-instruct',
        'display_name': 'Qwen 3 4B',
        'description': 'Dual thinking / non-thinking; instruction-following, agent workflows',
        'context_length': 128000,
        'parameters': '4B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'nvidia/llama-3.1-nemotron-ultra-253b-v1',
        'display_name': 'NVIDIA Llama 3.1 Nemotron Ultra 253B v1',
        'description': 'Advanced reasoning, RAG, tool-calling (needs explicit reasoning prompt)',
        'context_length': 128000,
        'parameters': '253B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'deepseek/deepseek-r1-distill-qwen-14b',
        'display_name': 'DeepSeek R1 Distill Qwen 14B',
        'description': 'Distilled from R1; strong math & code (AIME 69.7, MATH-500 93.9)',
        'context_length': 64000,
        'parameters': '14B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'meta-llama/llama-3.2-3b-instruct',
        'display_name': 'Meta Llama 3.2 3B Instruct',
        'description': '8 languages; dialogue, reasoning, summarization',
        'context_length': 131000,
        'parameters': '3B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'meta-llama/llama-3.1-405b-instruct',
        'display_name': 'Meta Llama 3.1 405B Instruct',
        'description': 'High-quality dialogue; rivals GPT-4o & Claude 3.5',
        'context_length': 131000,
        'parameters': '405B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'deepseek/deepseek-v3-0324',
        'display_name': 'DeepSeek V3 0324',
        'description': 'Latest V3; strong all-round performance',
        'context_length': 16000,
        'parameters': '685B MoE',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'deepseek/deepseek-r1-0528',
        'display_name': 'DeepSeek R1 0528',
        'description': 'Open reasoning tokens; MIT-licensed update of R1',
        'context_length': 64000,
        'parameters': '671B MoE (37B active)',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'deepseek/deepseek-r1',
        'display_name': 'DeepSeek R1',
        'description': 'Performance on par with OpenAI o1; fully open source',
        'context_length': 64000,
        'parameters': '671B MoE (37B active)',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'deepseek/deepseek-v3',
        'display_name': 'DeepSeek V3',
        'description': 'Pre-trained on 15 T tokens; rivals closed models',
        'context_length': 64000,
        'parameters': '685B MoE',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'cypher/cypher-alpha',
        'display_name': 'Cypher Alpha',
        'description': 'Long-context general model; provider logs prompts & outputs',
        'context_length': 1000000,
        'parameters': 'Unknown',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'tng/deepseek-r1t-chimera',
        'display_name': 'TNG DeepSeek R1T Chimera',
        'description': 'Combines R1 reasoning with V3 efficiency; MIT licence',
        'context_length': 64000,
        'parameters': 'MoE merge',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'google/gemini-2.0-flash-experimental',
        'display_name': 'Google Gemini 2.0 Flash Experimental',
        'description': 'Very fast TTFT; multimodal, coding, complex instructions, function calling',
        'context_length': 1050000,
        'parameters': 'Unknown',
        'modality': 'multimodal',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'qwen/qwq-32b-preview',
        'display_name': 'Qwen QwQ 32B',
        'description': 'Medium-size reasoning model; competitive with DeepSeek R1',
        'context_length': 33000,
        'parameters': '32B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    },
    {
        'model_id': 'mistralai/mistral-nemo',
        'display_name': 'Mistral Nemo',
        'description': 'Multilingual (11 langs), 128 K context, function calling (Apache 2.0)',
        'context_length': 131000,
        'parameters': '12B',
        'modality': 'text',
        'pricing': {'prompt': 0, 'completion': 0},
        'is_free': True
    }
]

def add_new_openrouter_models():
    """Aggiunge i nuovi modelli OpenRouter gratuiti al database"""
    
    app = create_app()
    with app.app_context():
        # Controlla quali modelli esistono già
        existing_models = {model.model_id for model in OpenRouterModel.query.all()}
        
        print("🔍 AGGIUNTA NUOVI MODELLI OPENROUTER")
        print("="*50)
        print(f"Modelli esistenti nel DB: {len(existing_models)}")
        print(f"Nuovi modelli da aggiungere: {len(NEW_FREE_MODELS)}")
        print("-" * 50)
        
        added_count = 0
        skipped_count = 0
        
        for model_data in NEW_FREE_MODELS:
            model_id = model_data['model_id']
            
            if model_id in existing_models:
                print(f"⏭️  SKIP: {model_data['display_name']} (già esistente)")
                skipped_count += 1
                continue
            
            # Crea nuovo modello
            new_model = OpenRouterModel(
                model_id=model_id,
                name=model_data['display_name'],
                description=model_data['description'],
                context_length=model_data['context_length'],
                pricing_prompt=model_data['pricing'].get('prompt', 0.0) if model_data['pricing'] else 0.0,
                pricing_completion=model_data['pricing'].get('completion', 0.0) if model_data['pricing'] else 0.0,
                is_free=model_data['is_free']
            )
            
            try:
                db.session.add(new_model)
                db.session.commit()
                print(f"✅ AGGIUNTO: {model_data['display_name']}")
                added_count += 1
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ ERRORE aggiungendo {model_data['display_name']}: {str(e)}")
        
        print("-" * 50)
        print(f"📊 RIEPILOGO:")
        print(f"  ✅ Modelli aggiunti: {added_count}")
        print(f"  ⏭️  Modelli saltati (esistenti): {skipped_count}")
        
        # Verifica finale
        total_models = OpenRouterModel.query.count()
        free_models = OpenRouterModel.query.filter_by(is_free=True).count()
        
        print(f"  📈 Totale modelli nel DB: {total_models}")
        print(f"  🆓 Modelli gratuiti: {free_models}")
        
        print("\n🎉 Aggiornamento completato!")

def list_all_free_models():
    """Lista tutti i modelli gratuiti nel database"""
    
    app = create_app()
    with app.app_context():
        free_models = OpenRouterModel.query.filter_by(is_free=True).order_by(OpenRouterModel.name).all()
        
        print(f"\n📋 TUTTI I MODELLI GRATUITI ({len(free_models)})")
        print("="*60)
        
        for model in free_models:
            ctx_str = f"{model.context_length:,}" if model.context_length else "N/A"
            print(f"• {model.name}")
            print(f"  ID: {model.model_id}")
            print(f"  Params: {model.parameters} | Ctx: {ctx_str}")
            print(f"  {model.description[:80]}{'...' if len(model.description) > 80 else ''}")
            print()

if __name__ == "__main__":
    print("🚀 AGGIORNAMENTO MODELLI OPENROUTER 2025")
    print("="*50)
    
    # Aggiungi nuovi modelli
    add_new_openrouter_models()
    
    # Lista tutti i modelli gratuiti
    list_all_free_models()
