#!/bin/bash
# Wrapper to enforce PATH for yt-dlp
# Assumes running from Project Root

PROJECT_ROOT=$(pwd)
export PATH="$PROJECT_ROOT/.venv/bin:$PATH"

# Debug
# echo "WRAPPER PATH: $PATH" >&2
# node --version >&2

# Check for Deno first (preferred by yt-dlp)
DENO_BIN="$HOME/.deno/bin/deno"
NODE_BIN=$(which node)

if [ -f "$DENO_BIN" ]; then
    # Use Deno with enabled remote components (critical for challenge solving)
     echo "WRAPPER EXEC (Deno): $PROJECT_ROOT/.venv/bin/yt-dlp --js-runtimes deno:$DENO_BIN --remote-components ejs:github $@" >&2
     exec "$PROJECT_ROOT/.venv/bin/yt-dlp" --js-runtimes "deno:$DENO_BIN" --remote-components ejs:github "$@"
     
elif [ -n "$NODE_BIN" ]; then
    # Fallback to Node (resolve symlink)
    NODE_BIN=$(readlink -f "$NODE_BIN")
    echo "WRAPPER EXEC (Node): $PROJECT_ROOT/.venv/bin/yt-dlp --js-runtimes node:$NODE_BIN $@" >&2
    exec "$PROJECT_ROOT/.venv/bin/yt-dlp" --js-runtimes "node:$NODE_BIN" "$@"
else
    exec "$PROJECT_ROOT/.venv/bin/yt-dlp" "$@"
fi
