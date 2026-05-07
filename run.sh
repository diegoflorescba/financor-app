#!/bin/bash
source venv/bin/activate

PORT="${PORT:-5000}"

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "El puerto $PORT está en uso. Usando 5001 para evitar conflicto."
  PORT=5001
fi

export PORT
python3 app.py
