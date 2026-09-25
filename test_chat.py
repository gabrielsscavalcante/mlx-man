import mlx_lm
model, tokenizer = mlx_lm.load("mlx-community/Qwen2.5-7B-Instruct-4bit")
print(hasattr(tokenizer, 'apply_chat_template'))
messages = [{"role": "user", "content": "Hello"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print(prompt)
