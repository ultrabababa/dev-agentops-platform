<!-- SPDX-License-Identifier: Apache-2.0 -->
# tan

[![ci](https://github.com/alplabai/tan-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/alplabai/tan-cli/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/alplabai/tan-cli?sort=semver)](https://github.com/alplabai/tan-cli/releases/latest)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

**The standalone Alp Lab build CLI.** `tan` consumes the alp-sdk *build-plan* and
executes it — it is the single executor and the user command surface for
building, flashing, and inspecting Alp Lab E1M / E1M-X firmware.

`bootstrap` / `build` / `run` / `size` / `image` / `flash` / `clean` / `renode`
are native Rust — `bootstrap` included, so there is no `bash` dependency and
native Windows is a first-class host. Only `migrate` / `lock` / `quality` still
forward to `west alp-*`, and
`model` / `monitor` / `new-som` / `faultdecode` to the SDK `alp` CLI. Licensed
**Apache-2.0** (see [`LICENSE`](LICENSE); the SPDX identifier is also set in each
`Cargo.toml` and source header).

## Install

Every version tag publishes a raw, uncompressed binary per platform.

### Automatic (recommended)

The install scripts detect your platform, download the matching binary, and put
`tan` on your PATH. They install **user-local by default — no `sudo`/admin**
(`~/.local/bin` on Unix; `%LOCALAPPDATA%\Programs\tan` + your user PATH on
Windows). Add `--system` / `-System` for a system-wide install (that path needs
elevated permission).

On Unix, if the install dir is not already on PATH, the script appends one line
to your login shell's rc (`~/.zshrc` / `~/.bash_profile` / `~/.profile`) — with a
printed notice, idempotently — so `tan` works in a new shell (this is what makes a
no-sudo install global on macOS, where `~/.local/bin` isn't on the default PATH).
Pass `--no-modify-path` to skip it. On Windows the script already updates your
user PATH.

```sh
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/alplabai/tan-cli/main/install.sh | sh
# system-wide (/usr/local/bin, uses sudo):   curl -fsSL …/install.sh | sh -s -- --system
```

```powershell
# Windows (PowerShell)
irm https://raw.githubusercontent.com/alplabai/tan-cli/main/install.ps1 | iex
# system-wide (%ProgramFiles%, run in an elevated PowerShell):   … ; .\install.ps1 -System
```

### Manual

Pick the asset for your host (full table in [`docs/release-contract.md`](docs/release-contract.md)).

**Verify the digest — the scripts refuse to install without it, and so should
you.** Two rules the installers follow and these snippets follow too: pin the
tag ONCE and build both URLs from it (resolving `latest` separately for the
binary and for `checksums.txt` can straddle a release and check one release's
bytes against another's digests — the digest for a given filename really does
move between tags), and do not put the binary in place until it matches.
`tan --version` is not a check: it proves something runs, not that it is what
we published.

Each snippet resolves `latest` **once** into `TAG`/`$Tag` — the same tag the
one-liners above resolve — and downloads into a **fresh directory**, so a failed
fetch can never leave you verifying a previous tag's leftovers and getting a
confident `OK`. Set the variable to an explicit `vX.Y.Z` from the
[releases page](https://github.com/alplabai/tan-cli/releases) to pick a
different one. (`latest` skips pre-releases, so it is not always the highest
version number.)

**Linux / macOS**

```sh
# Resolve latest ONCE (or set TAG=vX.Y.Z yourself), same redirect install.sh follows.
TAG=$(curl -fsSLI -o /dev/null -w '%{url_effective}' \
  https://github.com/alplabai/tan-cli/releases/latest | sed 's#.*/tag/##')
ASSET=tan-x86_64-unknown-linux-musl   # swap for your platform; musl = static, any distro
BASE=https://github.com/alplabai/tan-cli/releases/download/$TAG

# macOS has shasum, not sha256sum -- pick whichever is present.
SHA=sha256sum; command -v $SHA >/dev/null 2>&1 || SHA="shasum -a 256"

# Chained: a failed fetch stops the sequence instead of verifying a stale file.
d=$(mktemp -d) &&
curl -fsSL -o "$d/$ASSET" "$BASE/$ASSET" &&
curl -fsSL -o "$d/checksums.txt" "$BASE/checksums.txt" &&
line=$(awk -v a="$ASSET" '$2 == a' "$d/checksums.txt") &&
[ -n "$line" ] &&
printf '%s\n' "$line" | (cd "$d" && $SHA -c -) &&
chmod +x "$d/$ASSET" &&
sudo mv "$d/$ASSET" /usr/local/bin/tan &&
tan --version
```

The verify step prints `<asset>: OK`. Every other outcome stops the chain and
installs nothing: a failed download, an asset missing from `checksums.txt` (the
`[ -n "$line" ]` guard — `sha256sum -c` exits **0** on empty input, so piping an
empty match straight into it would pass), and a digest mismatch (`FAILED`).
Failures are silent apart from the tool's own message; run the steps one at a
time if you need to see which stopped it.

**Windows (PowerShell)**

```powershell
# Stop on the first failed fetch, and negotiate TLS 1.2 -- Windows PowerShell 5.1
# still defaults to protocols github.com refuses. Both mirror install.ps1.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Resolve latest ONCE (or set $Tag = 'vX.Y.Z'), same API field install.ps1 reads.
$Tag   = (Invoke-RestMethod -Uri 'https://api.github.com/repos/alplabai/tan-cli/releases/latest' -UseBasicParsing).tag_name
$Asset = 'tan-x86_64-pc-windows-msvc.exe'
$Base  = "https://github.com/alplabai/tan-cli/releases/download/$Tag"

# Fresh dir, never the destination: a bad binary written straight to tan.exe has
# already landed, and may already be locked or on PATH.
$d = (New-Item -ItemType Directory -Path (Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid()))).FullName
Invoke-WebRequest -Uri "$Base/$Asset" -OutFile "$d\$Asset" -UseBasicParsing
Invoke-WebRequest -Uri "$Base/checksums.txt" -OutFile "$d\checksums.txt" -UseBasicParsing

# Exact field match, same as install.ps1 -- a substring match would accept a
# neighbouring asset's line.
$want = Get-Content -LiteralPath "$d\checksums.txt" | ForEach-Object {
  $p = $_ -split '\s+', 2
  if ($p.Count -eq 2 -and $p[1].Trim() -eq $Asset) { $p[0].Trim().ToLower() }
} | Select-Object -First 1
$got = (Get-FileHash -LiteralPath "$d\$Asset" -Algorithm SHA256).Hash.ToLower()

# Two different facts, deliberately worded apart: an incomplete release is not
# a tampered download.
if (-not $want) { throw "$Asset is not listed in $Tag's checksums.txt -- the release is incomplete. Nothing installed." }
if ($got -ne $want) { throw "SHA256 MISMATCH for $Asset ($Tag): expected $want, got $got. Nothing installed." }

# Only now put it in place. This is where install.ps1 puts it.
$dest = "$env:LOCALAPPDATA\Programs\tan"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Move-Item -LiteralPath "$d\$Asset" -Destination "$dest\tan.exe" -Force
& "$dest\tan.exe" --version   # add $dest to your user PATH to run `tan` from a new shell
```

**Stronger, when you have [`gh`](https://cli.github.com/):** every asset —
`checksums.txt` and `envelope-contract.json` included — carries a GitHub
build-provenance attestation.

```sh
gh attestation verify <downloaded-file> --repo alplabai/tan-cli \
  --signer-workflow alplabai/tan-cli/.github/workflows/release.yml
```

Both are documented rather than one, because they answer different questions.
sha256 proves the bytes match what is published beside them and needs nothing
but coreutils (or PowerShell's built-in `Get-FileHash`) — so it is the baseline
every host can run, including one that cannot install `gh`. The attestation
proves the file came out of a GitHub Actions run in this repo; `--signer-workflow`
is what narrows that to the release workflow specifically, rather than any
workflow here. Neither is implied by the other: a digest published in the same
release says nothing about who built it. Run the digest check always; add the
attestation when `gh` is available. Details in
[`docs/release-contract.md`](docs/release-contract.md).

**From source** (Rust **1.86+**, edition 2024):

```sh
git clone https://github.com/alplabai/tan-cli && cd tan-cli
cargo install --path crates/tan-cli --locked
```

### Package managers

> [!WARNING]
> **Neither package-manager path resolves yet.** The release workflow's
> crates.io and npm publish jobs have never run with a token, so no version of
> `alp-tan-cli` exists on crates.io and no version of `@alplabai/tan` exists on
> npm — both jobs reported success while publishing nothing
> ([#151](https://github.com/alplabai/tan-cli/issues/151)). Use the release
> binaries above, or build from source. The commands below are the contract
> these channels will honour once the tokens are configured; they are documented
> now so the naming does not change under anyone later.

**crates.io** (Rust **1.86+**, edition 2024) — the published crate is named
`alp-tan-cli` (`tan`/`tan-cli` were already taken on crates.io by an unrelated
project); the installed binary is still `tan`:

```sh
cargo install alp-tan-cli --locked
tan --version
```

**npm** — a shim that downloads the matching platform binary on install (see
[`npm-shim/`](npm-shim/)); no Rust toolchain needed:

```sh
npm install -g @alplabai/tan
# or run without installing:
npx @alplabai/tan --version
```

`tan` needs an **alp-sdk checkout** to plan against. It is found, in order, from
`--sdk-root <path>`, the `.alp/sdk-path` pointer `tan sdk switch` writes, or an
`alp-sdk/` directory beside the project. `tan sdk install <version>` only
downloads into `~/.alp/sdk-cache` — follow it with `tan sdk switch <version>` to
select it (which also reconciles a stale `.west/config` manifest pointer left
over from a prior SDK version under the same workspace topdir). No VS Code
required.

## Quickstart

```sh
# Start in a directory holding an alp-sdk checkout — clone one, or
# `tan sdk install <version> && tan sdk switch <version>`.
tan bootstrap --sdk-root ./alp-sdk    # west + Zephyr workspace + Python deps
                                      # (Linux, macOS and native Windows alike)
tan init --name my-app                # defaults to --template zephyr-app
                                      # --som E1M-AEN801
cd my-app                             # sibling ../alp-sdk resolves automatically

tan validate                          # schema + semantic checks on board.yaml
tan build                             # plan → materialise → per-core slice build
tan size                              # footprint vs the SoM memory budget
tan run --flash                       # build, then run (host) or program (hardware)
```

`tan doctor` sanity-checks the host: build readiness (SDK, Zephyr workspace,
west) alongside debug readiness for the selected target/server. `tan doctor
--build --fix` goes further, resolving the OS set from `board.yaml` and
diagnosing (and repairing what it can) a build environment that is not ready;
`--fix` requires `--build`. `tan completion --shell zsh` emits a completion
script.

`bootstrap` runs natively on Linux, macOS and Windows and needs no `bash`; it
names the missing prerequisites rather than installing system packages itself.
The install commands come from the SDK's own `metadata/bootstrap.json`
(`prerequisites.install`, keyed per OS), not from a table `tan` carries — so
Windows prints the `winget install` line for a missing `git`/`cmake`/`python`/
`ninja`, and the JSON envelope's `missingPrerequisites[].command` now carries
real `apt-get`/`brew` commands on Linux and macOS where it used to be `null` on
every POSIX host. The *printed* POSIX refusal line is deliberately unchanged —
it stays `bootstrap.sh`'s verbatim, naming the tools and nothing else. An SDK
too old to carry `prerequisites.install` falls back to the same commands, so no
host loses one.

Zephyr and baremetal cores build on every host. Only a project whose cores are
*all* Yocto is refused off Linux — a mixed board still bootstraps, with a
warning that the Yocto core itself needs WSL2 or a Linux host.

`west init -l` puts the workspace (`zephyr/`, `modules/`, `.west/`, the venv)
beside the alp-sdk checkout — its PARENT directory. If that parent holds
ANY other entry besides the checkout itself — dotfiles included; a stray
`.DS_Store`/`Thumbs.db`/`.gitignore` counts too, not just an obvious risk like
cloning into `~/Downloads` or `$HOME` — `bootstrap` guards it instead of
spraying multiple gigabytes there unannounced: interactively it offers to
move the checkout into a dedicated `alp-workspace/` sibling; under a
non-interactive stdio (`--non-interactive`/`--ci`/`--format json`, or stdin or
stderr is simply not a terminal — piped, redirected, or a CI runner) it refuses
outright, naming the fix. If a dedicated parent is inconvenient, the one-line
answer is `tan bootstrap --workspace <path>` — no guard, no prompt, workspace
built there. A parent already holding a REAL `.west` workspace (a readable
`.west/config`, not merely an entry named `.west`) is never guarded, and
bootstrap's own venv from an earlier, interrupted run is never counted as
foreign content either.

## Commands

| Area | Commands |
| --- | --- |
| **Project** | `init` · `scaffold` · `examples` · `explain` · `presets` · `pinmux` |
| **Configure & verify** | `validate` · `generate` · `diff` · `inspect` · `trace` · `doctor` · `debug-config` · `support-bundle` · `kconfig` |
| **Build & run** (native) | `build` · `run` · `flash` · `image` · `size` · `clean` · `renode` |
| **Environment** (native) | `bootstrap` · `sdk` · `completion` |
| **Forwarders** | `migrate` · `lock` · `quality` → `west alp-*`; `model` · `monitor` · `new-som` · `faultdecode` → `python -m alp_cli` |

`tan <command> --help` for flags. Global flags apply to every command:

| Flag | Effect |
| --- | --- |
| `--project <PATH>` | Project root (default: current directory). |
| `--board-yaml <PATH>` | Explicit `board.yaml`, overriding project resolution. |
| `--sdk-root <PATH>` | alp-sdk checkout to plan against. |
| `--format json` | Machine-readable envelope instead of text. |
| `--non-interactive` | Never prompt. A command with a documented default takes it (`init` scaffolds `zephyr-app` into `.`); one without fails naming the missing flag (`scaffold` needs `--name`). Applied unasked when stdin or stderr is not a terminal — piped, redirected, or a CI runner (#187). |
| `--ci` | Implies `--non-interactive` and disables color. |
| `--quiet` / `--verbose` / `--no-color` | Output volume and styling. |

`--format json` emits the stable envelope
`{command, ok, exitCode, project, sdk, data, issues}` — the contract the
alp-sdk-vscode extension consumes (`sdk` is optional: present only when the
command actually resolved an alp-sdk root). Text output is for humans and may
change; the envelope is the API.

## Where it sits (three repos, one executor)

```
 alp-sdk-vscode  ──shells──►  tan (this repo)  ──drives──►  alp-sdk
 (VS Code ext)                (executor + CLI)              (planner + libs)
```

- **alp-sdk** — the planner + libraries. Emits the machine-readable *build-plan*
  (`python -m alp_orchestrate --emit build-plan`). Ships an `alp` console script
  (plus `alp-mcp`) and the `west alp-*` commands `tan` forwards to (see
  Forwarders below) — it is not a user-facing CLI surface in its own right.
- **tan** — this repo. Consumes the plan and executes each per-core slice
  (`west` / `bitbake` / `cmake`), owns skip-vs-fail, env application, scheduling,
  progress UX, SDK version management, and the manifest it reads back for
  flash/size/image. **What a standalone SDK user installs — no VS Code needed.**
- **alp-sdk-vscode** — a thin extension intended to shell `tan`; as of this
  writing the extension still resolves/downloads a binary named `alp`
  (`SUPPORTED_CLI_VERSION` 0.2.0) — the repoint to `tan` is pending.

Dependency direction is one-way: **extension → tan → alp-sdk.** Installing `tan`
never drags in the extension. The user-facing command / binary is `tan`, not
`alp` (RFC #837).

## The seam: the build-plan

`tan` reads SDK internals through exactly one contract — the build-plan JSON
(`metadata/schemas/build-plan-v1.schema.json` in alp-sdk). `tan-core`'s
`build_plan.rs` models the consumer side. Two guarantees the ADR pins:

- **Version-skew guard** — `tan` rejects a plan whose `schemaVersion` it doesn't
  support instead of silently falling back to hand-ported behaviour. That silent
  fallback is exactly the drift RFC #843 fixed; skew must not re-introduce it.
- **`env` vs `envAppendPath`** — `env` is set verbatim; `envAppendPath` is
  appended (os.pathsep) *only if not already present*, so a consumer that
  resolves those paths itself is not silently overridden ("plan wins / CLI fills
  gaps").

A build writes `build/system-manifest.yaml` — the post-build IDE/tool contract
(per-core slices, IPC, helper MCUs) that `flash` / `image` / `size` / `renode`
read back.

## Workspace layout

A Cargo workspace; pure logic lives in `tan-core`, all IO and subprocess
execution in `tan-cli`:

```
Cargo.toml                     # [workspace] + [workspace.dependencies] + [profile.release]
crates/
  tan-core/                    # pure domain logic (no IO)
    src/build_plan.rs          #   build-plan consumer contract + version-skew guard
    src/system_manifest.rs     #   post-build manifest parse/overlay/serialize
    src/plan_exec.rs           #   pure env-append + skip/fail-policy decisions
    src/{flash,debug,wizard,sdk_catalogue}/   #   backends, reports, templates, presets
  tan-cli/                     # the `tan` binary — arg parsing, IO, subprocess exec
    src/{main,cli,envelope,exit}.rs
    src/commands/{build,run,flash,init}/          #   module dirs
    src/commands/{sdk,doctor,validate,…}.rs
```

`tan-core` is `alp-core` ported faithfully (symbol names preserved; only the
crate name and cosmetic `alp`-branding changed). `build_plan.rs` additionally
carries the newer ADR-0020 fields the SDK now emits — per-slice
`envAppendPath` and the top-level `executionPolicy`.

## Development

Four gates, all of them, before every push. CI runs `fmt` + `clippy` once on
Linux, matrixes `build` + `test` across Linux, Windows, and macOS, and adds an
`msrv` job that re-checks the declared `rust-version` (1.86):

```sh
cargo fmt --all --check
cargo clippy --all-targets -- -D warnings
cargo build --all-targets
cargo test
```

House rules: keep files small, put pure logic in `tan-core` (with unit tests)
rather than the executor, and never rename an SDK-contract string
(`alp-sdk`, `alp_orchestrate`, `board.yaml`, `alp.conf`, `.alp/…`) — only the
user-facing binary is `tan`.

## Releases

Version-tag pushes (`v<major>.<minor>.<patch>`) build per-platform `tan`
binaries and publish them as GitHub release assets for the alp-sdk-vscode
downloader. The tag must equal the workspace `Cargo.toml` version — CI fails the
release otherwise. The exact tag scheme, per-target asset names, and the vscode
`releaseAssetForTarget` mapping are the release-asset contract — see
[`docs/release-contract.md`](docs/release-contract.md).

## References

- alp-sdk **ADR-0020** (the decision this implements)
- **RFC #843** (the drift that motivated it): alplabai/alp-sdk#843
- **RFC #837** (`alp` → `tan` naming): alplabai/alp-sdk#837
