# export CUDA_VISIBLE_DEVICES=0
# export NCCL_P2P_DISABLE=1
# lm_eval --model vllm \
#     --model_args pretrained=Qwen/Qwen3-8B,tensor_parallel_size=1,data_parallel_size=1,gpu_memory_utilization=0.7 \
#     --tasks tower_of_hanoi \
#     --device cuda \
#     --batch_size 8 \
#     --log_samples \
#     --output_path ./results/tower_of_hanoi_results.jsonl \
lm_eval --model openai-chat-completions \
    --model_args model=gpt-5.1,num_concurrent=8  \
    --tasks tower_of_hanoi \
    --apply_chat_template true \
    --batch_size 8 \
    --log_samples \
    --output_path ./results/tower_of_hanoi_results_openai_chat_completions.jsonl \