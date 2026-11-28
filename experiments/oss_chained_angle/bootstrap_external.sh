#!/usr/bin/env bash
# Fetch unmodified, license-preserved upstream source dependencies.
# These are build-time checkouts, not submitted competition KMBs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="${1:-$ROOT/external/oss_chained_angle}"
mkdir -p "$DEST"
checkout() {
  local ownerrepo="$1" commit="$2" name="$3"
  if [[ ! -d "$DEST/$name/.git" ]]; then
    git clone --filter=blob:none "https://github.com/$ownerrepo.git" "$DEST/$name"
  fi
  git -C "$DEST/$name" fetch origin "$commit"
  git -C "$DEST/$name" checkout --detach "$commit"
  echo "PINNED $name $commit"
}
checkout manwithacat/vqcc-tools cd4b30f6806b13096ab0d30946f38c8c9548dfa7 vqcc-tools
checkout manwithacat/kickmix-engine 166b61d2e0a7404ace8acf62a6f269105e6b97f1 kickmix-engine
checkout lsils/mockturtle a3f817de4005ee6ae12b4dd1ffcf4a4f910691d7 mockturtle
checkout gmeuli/caterpillar 4c6f766cd0ffc62d37ab45edfe80c9f1eae44764 caterpillar
echo "All pinned source checkouts complete; inspect each LICENSE/NOTICE."
echo "Optional: (cd \"$DEST/kickmix-engine\" && cargo test -p qrom-plan && cargo build --release -p qrom-plan)"
