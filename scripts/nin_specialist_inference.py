from unsloth import FastLanguageModel
import torch

max_seq_length = 2048
dtype = None
load_in_4bit = True

model_path = "/home/lucy-ubuntu/Escritorio/NIN/entrenamiento/nin_specialist_lora"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_path, # Carga el modelo base + el adaptador LoRA
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
FastLanguageModel.for_inference(model) # 2x más rápido para inferencia

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Context:
{}

### Response:
{}"""

def ask_nin(instruction, context=""):
    inputs = tokenizer(
    [
        alpaca_prompt.format(instruction, context, "")
    ], return_tensors = "pt").to("cuda")

    outputs = model.generate(**inputs, max_new_tokens = 512, use_cache = True)
    return tokenizer.batch_decode(outputs)[0]

if __name__ == "__main__":
    test_q = "Crea un workflow de n8n para enviar alertas de temperatura a Telegram."
    print(f"Pregunta: {test_q}")
    response = ask_nin(test_q)
    print(f"Respuesta:\n{response}")
