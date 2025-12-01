lm_eval --model hf \
    --model_args pretrained=Qwen/Qwen3-8B \
    --tasks tower_of_hanoi \
    --device cpu \
    --batch_size 8