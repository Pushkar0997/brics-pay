#!/usr/bin/env bash
# PreToolUse hook: agents may not edit CONTRACT.md or secret files.
# CONTRACT changes need human approval (see CONTRACT.md, "Changing this file").
# Exit 2 blocks the tool call and shows the message to the agent.
input="$(cat)"
path="$(printf '%s' "$input" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)"
case "$path" in
  *CONTRACT.md)
    echo "CONTRACT.md requires human approval. Do not edit it. Propose the change as a new entry in spec/decisions.md with Status: proposed, then stop and ask." >&2; exit 2 ;;
  *.env|*.env.*)
    case "$path" in *.env.example) exit 0 ;; esac
    echo "Never write secrets to tracked files. Ask the human where this credential should come from." >&2; exit 2 ;;
esac
exit 0
