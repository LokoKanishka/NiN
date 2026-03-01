from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported
import os

# 1. Configuración del Modelo
max_seq_length = 2048
dtype = None # None auto detecta
load_in_4bit = True # Usamos 4bit para eficiencia

model_name = "unsloth/Llama-3.2-3B-Instruct"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# 2. Configuración LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = "unsloth", # Muy importante para VRAM
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# 3. Formateo de Datos
# Usamos el dataset generado anteriormente
alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Context:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    contexts      = examples["context"]
    outputs      = examples["response"]
    texts = []
    for instruction, context, output in zip(instructions, contexts, outputs):
        text = alpaca_prompt.format(instruction, context, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }

dataset = load_dataset("json", data_files={"train": "/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/dataset/colmena_core_v1.jsonl"}, split="train")
dataset = dataset.map(formatting_prompts_func, batched = True,)

# 4. Entrenamiento
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Suficiente para un dataset pequeño de 28 ejemplos
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/outputs",
    ),
)

# 5. Ejecutar
print("🚀 Iniciando entrenamiento LoRA...")
trainer_stats = trainer.train()

# 6. Guardar el Adaptador
print("💾 Guardando adaptador LoRA...")
model.save_pretrained("/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/nin_specialist_lora")
tokenizer.save_pretrained("/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/nin_specialist_lora")

print("✅ Fine-tuning completado con éxito.")
