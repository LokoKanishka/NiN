from huggingface_hub import HfApi

api = HfApi()
# Removing "gguf" filter just to see if the base model exists
models = api.list_models(search="120b", limit=10, sort="downloads", direction=-1)

print("Found models:")
for model in models:
    print(f"- {model.modelId} ({model.downloads} downloads)")
