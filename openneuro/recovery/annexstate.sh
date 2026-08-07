#!/bin/bash
# Why does `git annex whereis` report 0 copies? Inspect the location log state.
#   bash annexstate.sh <clone dir> [key]
CLONE="${1:?usage: annexstate.sh <clone dir> [key]}"
KEY="${2:-SHA256E-s5179352--02ab1ccd8ef93aae4098f5dc30650dbf7d20cc061ccad38cde32faaf650a9a7f.sphere}"
cd "$CLONE" || exit 1

echo "=== refs ==="
git show-ref | grep -E 'git-annex|main' | head -6

echo "=== location logs in the annex branch ==="
for ref in git-annex origin/git-annex; do
  n=$(git ls-tree -r "$ref" --name-only 2>/dev/null | grep -c '\.log$')
  echo "  $ref: $n .log entries"
done

echo "=== is this key logged? ==="
echo "  key: $KEY"
# git-annex stores logs under hashdirlower(key)
for ref in git-annex origin/git-annex; do
  hit=$(git ls-tree -r "$ref" --name-only 2>/dev/null | grep -F "$KEY" | head -1)
  if [ -n "$hit" ]; then
    echo "  $ref -> $hit"
    echo "    content: $(git show "$ref:$hit" 2>/dev/null | head -2 | tr '\n' ' ')"
  else
    echo "  $ref -> NOT PRESENT"
  fi
done

echo "=== remote.log (which special remotes the dataset declares) ==="
git show git-annex:remote.log 2>/dev/null | cut -c1-120 || \
git show origin/git-annex:remote.log 2>/dev/null | cut -c1-120

echo "=== enabled remotes here ==="
git annex info 2>/dev/null | sed -n '/repositories:/,/transfers/p' | head -12
