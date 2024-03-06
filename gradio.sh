#!/bin/bash

# Modeles compatibles :
# /data/deepseek-coder-6.7b-instruct.Q4_K_M.gguf
# /data/deepseek-coder-6.7b-instruct.Q6_K.gguf
# /data/dolphin-2.6-mistral-7b-dpo-laser.Q4_K_M.gguf
# /data/mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf

cd /opt/matterbot/
source venv/bin/activate
python grinterface.py "/data/deepseek-coder-6.7b-instruct.Q4_K_M.gguf"
