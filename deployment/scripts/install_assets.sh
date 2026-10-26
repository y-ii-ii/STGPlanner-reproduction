#!/usr/bin/env bash
set -euo pipefail
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
base=/mnt/d/STGPlanner/models
checkout=/mnt/d/STGPlanner/downloads/gazebo_models
asset_ref=8163eb4b5e7e21985c6591d1c0bfb56468c0093f
mkdir -p "$base"
if [[ ! -d "$checkout/.git" ]]; then
  git -c http.proxy= -c https.proxy= clone --depth 1 --filter=blob:none --no-checkout \
    https://github.com/osrf/gazebo_models.git "$checkout"
fi
if ! git -C "$checkout" cat-file -e "$asset_ref^{commit}" 2>/dev/null; then
  git -C "$checkout" fetch --depth 1 origin "$asset_ref"
fi
git -C "$checkout" sparse-checkout init --cone
git -C "$checkout" sparse-checkout set grey_wall gazebo
git -C "$checkout" checkout --detach "$asset_ref"
cp -a "$checkout/grey_wall" "$checkout/gazebo" "$base/"
git -C "$checkout" rev-parse HEAD > /mnt/d/STGPlanner/logs/gazebo_models_commit.txt
cat >"$base/database.config" <<'EOF'
<?xml version="1.0"?>
<database><name>STGPlanner local models</name><models></models></database>
EOF
find "$base/grey_wall" "$base/gazebo" -type f -exec sha256sum {} \; > /mnt/d/STGPlanner/logs/model_checksums.txt
echo 'Official grey_wall and gazebo assets installed in the local model library.'
