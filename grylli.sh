#!/bin/bash
# grylli - Unified control script for Grylli project tasks

set -e

# Load .env if present
if [[ -f .env ]]; then
  export $(grep -v '^#' .env | xargs)
fi

# Optional: source aliases
[[ -f ~/.bash_aliases ]] && source ~/.bash_aliases

# ---------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------
dev() { ## Start Flask development server
  echo "🚀 Starting Flask development server..."
  python3 run.py
}

prod() { ## Start Gunicorn production server
  echo "🔥 Starting Gunicorn production server..."
  python3 -m gunicorn -c gunicorn.conf.py "app:create_app()"
}

help() { ## Show this help message
  echo -e "🛠  Available commands:\n"
  grep -E '^\w+\(\) \{ ## ' "$0" | while read -r line; do
    cmd=$(echo "$line" | cut -d '(' -f1)
    desc=$(echo "$line" | sed -E 's/^[^(]+\(\) \{ ## //')
    printf "  \033[36m%-12s\033[0m %s\n" "$cmd" "$desc"
  done
}

# ---------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------

if [[ $# -lt 1 ]]; then
  help
  exit 0
fi

cmd="$1"
shift

if declare -f "$cmd" > /dev/null; then
  "$cmd" "$@"
else
  echo "❌ Unknown command: $cmd"
  echo
  help
  exit 1
fi
