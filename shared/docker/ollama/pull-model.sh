#!/bin/sh
OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"
export OLLAMA_HOST
MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"
MAX_WAIT_SEC="${OLLAMA_PULL_MAX_WAIT_SEC:-300}"

echo "Waiting for Ollama at ${OLLAMA_HOST}..."
elapsed=0
while ! ollama list >/dev/null 2>&1; do
  if [ "$elapsed" -ge "$MAX_WAIT_SEC" ]; then
    echo "Ollama did not become ready within ${MAX_WAIT_SEC}s"
    exit 1
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

echo "Pulling model ${MODEL}..."
ollama pull "${MODEL}"
echo "Model ${MODEL} is ready."
