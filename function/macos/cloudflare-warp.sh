function setup-cloudflare-warp() {
  brew install --cask cloudflare-warp
  warp-cli registration new
  warp-cli connect
  warp-cli mode warp+doh
  warp-cli tunnel host add "*.tailscale.com"
  curl -s https://controlplane.tailscale.com/derpmap/default | jq -r '.Regions[] | .Nodes[] | [.IPv4, .IPv6] | @tsv' | while IFS=$'\t' read -r ipv4 ipv6; do
    warp-cli tunnel ip add "$ipv4" >/dev/null 2>&1
    warp-cli tunnel ip add "$ipv6" >/dev/null 2>&1
  done
}
