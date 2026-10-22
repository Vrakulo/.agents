#!/usr/bin/env bash
# 将 skill 软链到 OpenCode 的发现目录，重复执行安全。
set -euo pipefail

# 仓库位置由脚本自身推导，克隆到任意路径都能直接运行。
REPO="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
A="$HOME/.agents/skills"
O="$HOME/.config/opencode/skills"

mkdir -p "$A" "$O"

if git -C "$REPO" submodule status | grep -q '^-'; then
  echo "error: submodule 未初始化，先执行 git -C \"$REPO\" submodule update --init --recursive" >&2
  exit 1
fi

# 自有
ln -sfn "$REPO/skills/pr-feedback" "$A/pr-feedback"
ln -sfn "$REPO/skills/pull-request-rules" "$A/pull-request-rules"

# mattpocock/skills
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/pr" "$A/pr"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/code-review" "$A/code-review"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/codebase-design" "$A/codebase-design"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/domain-modeling" "$A/domain-modeling"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/grill-with-docs" "$A/grill-with-docs"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/productivity/grilling" "$A/grilling"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/implement" "$A/implement"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/implement-spec" "$A/implement-spec"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/retro" "$A/retro"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/setup-matt-pocock-skills" "$A/setup-matt-pocock-skills"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/tdd" "$A/tdd"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/to-spec" "$A/to-spec"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/to-tickets" "$A/to-tickets"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/wizard" "$A/wizard"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/productivity/writing-for-agents" "$A/writing-for-agents"
ln -sfn "$REPO/vendor/mattpocock-skills/skills/engineering/research" "$A/research"

# addyosmani/agent-skills
ln -sfn "$REPO/vendor/addyosmani-agent-skills/skills/performance-optimization" "$A/performance-optimization"
ln -sfn "$REPO/vendor/addyosmani-agent-skills/skills/deprecation-and-migration" "$A/deprecation-and-migration"
ln -sfn "$REPO/vendor/addyosmani-agent-skills/skills/code-review-and-quality" "$A/code-review-and-quality"
ln -sfn "$REPO/vendor/addyosmani-agent-skills/skills/code-simplification" "$A/code-simplification"

# wondelai/skills
ln -sfn "$REPO/vendor/wondelai-skills/clean-architecture" "$A/clean-architecture"
ln -sfn "$REPO/vendor/wondelai-skills/clean-code" "$A/clean-code"
ln -sfn "$REPO/vendor/wondelai-skills/pragmatic-programmer" "$A/pragmatic-programmer"
ln -sfn "$REPO/vendor/wondelai-skills/refactoring-patterns" "$A/refactoring-patterns"
ln -sfn "$REPO/vendor/wondelai-skills/software-design-philosophy" "$A/software-design-philosophy"
ln -sfn "$REPO/vendor/wondelai-skills/technical-documentation" "$A/technical-documentation"
ln -sfn "$REPO/vendor/wondelai-skills/working-with-legacy-code" "$A/working-with-legacy-code"

# phuryn/pm-skills
ln -sfn "$REPO/vendor/phuryn-pm-skills/pm-product-discovery/skills/brainstorm-ideas-existing" "$A/brainstorm-ideas-existing"

# cloudflare/skills
ln -sfn "$REPO/vendor/cloudflare-skills/skills/agents-sdk" "$O/agents-sdk"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/basin" "$O/basin"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/cf-cli" "$O/cf-cli"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/cloudflare" "$O/cloudflare"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/cloudflare-email-service" "$O/cloudflare-email-service"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/cloudflare-one" "$O/cloudflare-one"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/cloudflare-one-migrations" "$O/cloudflare-one-migrations"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/durable-objects" "$O/durable-objects"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/gateway-workers" "$O/gateway-workers"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/k2" "$O/k2"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/nextjs-on-cloudflare" "$O/nextjs-on-cloudflare"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/sandbox-migrate-to-next" "$O/sandbox-migrate-to-next"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/sandbox-next" "$O/sandbox-next"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/sandbox-stable" "$O/sandbox-stable"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/turnstile-spin" "$O/turnstile-spin"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/web-perf" "$O/web-perf"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/workers-best-practices" "$O/workers-best-practices"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/workers-profiling" "$O/workers-profiling"
ln -sfn "$REPO/vendor/cloudflare-skills/skills/wrangler" "$O/wrangler"

# web-infra-dev/midscene-skills
ln -sfn "$REPO/vendor/midscene-skills/skills/computer-automation" "$O/computer-automation"
ln -sfn "$REPO/vendor/midscene-skills/skills/vitest-midscene-e2e" "$O/vitest-midscene-e2e"
ln -sfn "$REPO/vendor/midscene-skills/skills/browser" "$O/browser-automation"
