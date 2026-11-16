---
name: container-runtime
description: Run a project's toolchain inside a container instead of on the host. Use when installing dependencies, building, testing, or starting a Rust, Java, Node.js, Flutter, Go, or Python project, or when the language is not yet in the image table and needs one.
---

# 容器化运行环境

项目命令默认在容器里执行：依赖安装、构建、测试、启动都走容器。本地工具链是退路，不是默认。

## 执行流程

1. **识别语言与项目根目录**。一个仓库可能有多种语言，每种语言单独跑一个容器。
2. **选镜像与版本**。查下面的对照表；表里没有的语言走「未列出的语言」。版本从项目配置读，不写死在本 skill 里。
3. **挂载目录**。项目根目录挂到容器工作目录，全局缓存目录挂到镜像内对应路径，临时文件落到 `.scratch/`。
4. **运行并清理**。每条命令一个容器，`--rm` 立即回收；需要常驻的服务用 `--name`，结束后显式删除。
5. **报告回退**。只有容器确实跑不了才用本地工具链，并说明原因与在宿主机执行过的命令。

## 镜像对照表

| 语言 | 镜像 | 标签 | 版本来源 |
| --- | --- | --- | --- |
| Rust | `rust` | `<major>.<minor>-slim`（glibc）或 `<major>.<minor>-alpine`（musl） | `rust-toolchain.toml` 的 `channel`、`Cargo.toml` 的 `rust-version` |
| Java | `eclipse-temurin` | `<major>-jdk-alpine`；只运行用 `<major>-jre-alpine` | `pom.xml` 的 `maven.compiler.release` / `java.version`、`build.gradle(.kts)` 的 toolchain、`.java-version` |
| Java（Maven 构建） | `maven` | `3-eclipse-temurin-<java-major>` | 同上 |
| Java（Gradle 构建） | `gradle` | `<gradle-major>-jdk<java-major>` | `gradle/wrapper/gradle-wrapper.properties`、`gradle.properties` |
| Node.js | `node` | `<major>-slim`；体积敏感时 `<major>-alpine` | `package.json` 的 `engines.node`、`.nvmrc`、`.node-version` |
| Flutter | `ghcr.io/cirruslabs/flutter` | `stable`；项目固定了版本时用完整版本（如 `3.24.5`） | `pubspec.yaml` 的 `environment.flutter`、`.fvmrc` |
| Go | `golang` | `<major>.<minor>-alpine` | `go.mod` 的 `go` 指令 |
| Python | `python` | `<major>.<minor>-slim`；需要 musl 才用 `<major>.<minor>-alpine` | `pyproject.toml` 的 `requires-python`、`.python-version`、`Pipfile` |

取版本的规则：

- 配置给的是下限（`>=3.11`、`go 1.22`、`^20`）时，取满足下限的最低版本。
- 标签粒度取镜像实际发布的粒度：Rust、Go、Python 取 `major.minor`，Java、Node.js 取 `major`。配置精确到 patch 而镜像没有该 tag 时，退到最近的 minor。
- 项目没有声明版本时先问用户，不要拿 `latest` 直接开跑。

镜像选择：

- 默认用 `slim`，`alpine` 只在体积敏感或明确需要 musl 时用。
- `alpine` 是 musl：Rust 需要 musl target，Python 缺少预编译 wheel，Java 原生库可能不兼容。这类失败先换 `slim`。
- Flutter 没有 Docker 官方镜像，`ghcr.io/cirruslabs/flutter` 是社区维护的事实标准镜像，使用前向用户说明。

## 全局缓存

| 语言 | 镜像内缓存路径 | 宿主机挂载来源 |
| --- | --- | --- |
| Rust | `$CARGO_HOME`（`/usr/local/cargo`） | `~/.cargo` |
| Java Maven | `~/.m2` | `~/.m2` |
| Java Gradle | `$GRADLE_USER_HOME`（`/home/gradle/.gradle`） | `~/.gradle` |
| Node.js | `$NPM_CONFIG_CACHE`（`/root/.npm`） | `~/.npm`；pnpm store、yarn cache 同理 |
| Go | `$GOMODCACHE`（`/go/pkg/mod`）、`$GOCACHE` | `~/go/pkg/mod`、`~/.cache/go-build` |
| Flutter | `$PUB_CACHE`（`/root/.pub-cache`） | `~/.pub-cache` |
| Python | `$PIP_CACHE_DIR`（`/root/.cache/pip`）、`$UV_CACHE_DIR` | `~/.cache/pip`、`~/.cache/uv` |

以宿主机 uid 运行时，镜像内的 root 家目录不可写：把所有缓存变量指到挂载点（如 `/cache/...`），或设 `HOME=/tmp`。

## 镜像源

默认使用 CERNET 镜像站 `https://mirrors.cernet.edu.cn/`；项目自带镜像配置时以项目为准。

### Rust

rustup 用环境变量：

```bash
-e RUSTUP_DIST_SERVER=https://mirrors.cernet.edu.cn/rustup \
-e RUSTUP_UPDATE_ROOT=https://mirrors.cernet.edu.cn/rustup/rustup
```

crates.io 没有等价环境变量，配置写在 `$CARGO_HOME/config.toml`。挂载 `~/.cargo` 后即宿主机同路径，自动生效：

```toml
[source.crates-io]
replace-with = 'mirror'

[source.mirror]
registry = "sparse+https://mirrors.cernet.edu.cn/crates.io-index/"

[registries.mirror]
index = "sparse+https://mirrors.cernet.edu.cn/crates.io-index/"
```

### Java

Maven 没有环境变量形式的 mirror，配置在 `~/.m2/settings.xml`；挂载 `~/.m2` 后自动生效。项目需要独立配置时用 `mvn -s <path>`。

```xml
<mirrors>
  <mirror>
    <id>aliyunmaven</id>
    <name>阿里云公共仓库</name>
    <url>https://maven.aliyun.com/repository/public</url>
    <mirrorOf>central</mirrorOf>
  </mirror>
</mirrors>
```

Gradle 不读 `settings.xml`，需要镜像时在 `init.gradle` 里替换 `repositories`；当前环境未配置，遇到慢下载先问用户。

以宿主机 uid 运行时，Java 从 `/etc/passwd` 推导 `user.home`，挂到 `/root/.m2` 不会被自动发现；显式传 `-Dmaven.repo.local=/root/.m2/repository -s /root/.m2/settings.xml`。

### Node.js

当前环境不配镜像源，使用官方 registry。需要时用 `-e NPM_CONFIG_REGISTRY=<url>`（pnpm 读同一变量，yarn 用 `YARN_NPM_REGISTRY_SERVER`）。

### Python

```bash
-e PIP_INDEX_URL=https://mirrors.cernet.edu.cn/pypi/web/simple \
-e UV_DEFAULT_INDEX=https://mirrors.cernet.edu.cn/pypi/web/simple
```

旧版 uv 用 `UV_INDEX_URL`。

### Flutter

```bash
-e PUB_HOSTED_URL=https://mirrors.cernet.edu.cn/dart-pub
```

### Go

```bash
-e GO111MODULE=on \
-e GOPROXY=https://goproxy.cn,direct
```

`GOSUMDB` 保持官方默认；命中私有模块时用 `GOPRIVATE` 排除，不要把 `GOSUMDB` 直接关掉。

## 运行模板

```bash
RUNTIME=$(command -v podman || command -v docker)
mkdir -p .scratch/tmp
$RUNTIME run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace \
  -v "$HOME/.cargo:/usr/local/cargo" \
  -v "$HOME/.rustup:/usr/local/rustup" \
  -e CARGO_HOME=/usr/local/cargo \
  -e RUSTUP_HOME=/usr/local/rustup \
  -e RUSTUP_DIST_SERVER=https://mirrors.cernet.edu.cn/rustup \
  -e RUSTUP_UPDATE_ROOT=https://mirrors.cernet.edu.cn/rustup/rustup \
  -v "$PWD/.scratch/tmp:/tmp" \
  rust:<major>.<minor>-slim \
  cargo test
```

- 一次性命令用 `--rm`；需要交互再加 `-it`。
- 常驻服务用 `--name <project>-<service>`，结束后 `$RUNTIME rm -f`。
- 临时文件通过把 `.scratch/tmp` 挂到 `/tmp` 留在 `.scratch/` 下。
- 项目已有 Dockerfile 或 compose 文件时直接复用，不另建镜像。
- 多语言项目按语言分别跑，例如 Node 前端 + Go 后端是两个容器。

其他语言按「镜像源」一节的取值补 `-e`；镜像标签里的 `<major>.<minor>` 从项目配置替换。Java 补 `-v "$HOME/.m2:/root/.m2"` 并显式传 `-Dmaven.repo.local`，Python 补 pip/uv 变量，Flutter 补 `PUB_HOSTED_URL`。

## 未列出的语言

1. 先查本地镜像：`$RUNTIME images --format '{{.Repository}}:{{.Tag}}'`，挑出与语言匹配的镜像。
2. 本地没有，查官方来源确定镜像名与标签：Docker Official Images 列表、Docker Hub、项目官方文档的容器安装页。
3. 把候选镜像名、版本、缓存路径、镜像源变量一并向用户确认；确认前不要运行。
4. 用户确认后，把新条目补进本 skill 的对照表。

## 回退到本地工具链

只有这些情况才回退，并说明原因：

- 没有可用的容器运行时。
- 需要宿主机特有资源：GPU、硬件设备、桌面环境、特定内核特性。
- 项目自身明确要求本地环境。

回退时报告在宿主机执行了哪些命令、为什么容器不可行。
