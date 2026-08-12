#!/usr/bin/env sh
# SPDX-License-Identifier: Apache-2.0
#
# tan installer for Linux + macOS. Downloads the prebuilt `tan` binary for this
# platform from GitHub Releases and installs it. By DEFAULT it installs to a
# user-local dir (~/.local/bin) so NO sudo/admin is needed. Pass --system to
# install to /usr/local/bin (that path needs elevated permission -> uses sudo).
#
#   curl -fsSL https://raw.githubusercontent.com/alplabai/tan-cli/main/install.sh | sh
#   ./install.sh [--version vX.Y.Z] [--dir <path>] [--system]
set -eu

REPO="alplabai/tan-cli"
VERSION="latest"
INSTALL_DIR="${TAN_INSTALL_DIR:-$HOME/.local/bin}"
MODIFY_PATH=1

while [ $# -gt 0 ]; do
	case "$1" in
	--version) VERSION="${2:?--version needs a value}"; shift 2 ;;
	--dir) INSTALL_DIR="${2:?--dir needs a value}"; shift 2 ;;
	--system) INSTALL_DIR="/usr/local/bin"; shift ;;
	--no-modify-path) MODIFY_PATH=0; shift ;;
	-h | --help)
		echo "usage: install.sh [--version vX.Y.Z] [--dir <path>] [--system] [--no-modify-path]"
		echo "  default install dir: \$HOME/.local/bin (no sudo). --system uses /usr/local/bin (sudo)."
		echo "  if the install dir is not already on PATH, the login shell's rc file is updated"
		echo "  (with a printed notice) so 'tan' works in any shell; --no-modify-path opts out."
		exit 0
		;;
	*) echo "install.sh: unknown argument: $1" >&2; exit 2 ;;
	esac
done

# host os -> rust target os part
os="$(uname -s)"
case "$os" in
Darwin) os_part="apple-darwin" ;;
# musl (static): no glibc floor, runs on any distro; TLS is rustls/ring so
# there are no extra runtime deps either. Only published from tan-cli
# v0.3.0 onward -- see the --version 404 note below.
Linux) os_part="unknown-linux-musl" ;;
*) echo "install.sh: unsupported OS '$os' -- on Windows use install.ps1" >&2; exit 1 ;;
esac

# host arch -> rust target arch part
arch="$(uname -m)"
case "$arch" in
arm64 | aarch64) arch_part="aarch64" ;;
x86_64 | amd64) arch_part="x86_64" ;;
*) echo "install.sh: unsupported architecture '$arch'" >&2; exit 1 ;;
esac

asset="tan-${arch_part}-${os_part}"

# One HTTP download, curl or wget, quiet about nothing. Both branches keep the
# flags they had inline before (`--proto '=https' --tlsv1.2`, and no -q on
# wget) -- the transport's own error IS the primary diagnostic, so it is never
# swallowed in favour of a guess.
download() { # $1 = url, $2 = output path; returns non-zero on failure
	if command -v curl >/dev/null 2>&1; then
		curl -fSL --proto '=https' --tlsv1.2 -o "$2" "$1"
	elif command -v wget >/dev/null 2>&1; then
		wget -O "$2" "$1"
	else
		echo "install.sh: need curl or wget on PATH" >&2
		exit 1
	fi
}

# `latest` is a REDIRECT, and resolving it twice is not the same as resolving
# it once: a release cut between the binary fetch and the checksums fetch would
# have us verify one release's asset against another release's digests. Rare,
# silent, and it produces a WRONG VERDICT rather than an error -- so pin the tag
# up front and build both URLs from it.
#
# The digest for a given filename really does move between tags: at v0.4.0-rc1
# `tan-x86_64-pc-windows-msvc.exe` is f159c1dc..., at v0.4.0 it is a80fb5da...,
# same asset name. Anything that caches or hardcodes a digest is wrong by
# construction; the digest must come from the tag the binary came from.
if [ "$VERSION" = "latest" ]; then
	echo "install.sh: resolving the latest release tag..."
	if command -v curl >/dev/null 2>&1; then
		resolved="$(curl -fsSL --proto '=https' --tlsv1.2 -o /dev/null \
			-w '%{url_effective}' "https://github.com/${REPO}/releases/latest" 2>/dev/null |
			sed -n 's#.*/releases/tag/##p')"
	else
		resolved="$(wget -S --spider --max-redirect=20 \
			"https://github.com/${REPO}/releases/latest" 2>&1 |
			sed -n 's#^[[:space:]]*Location:.*/releases/tag/\([^[:space:]]*\).*#\1#p' | tail -1)"
	fi
	if [ -z "${resolved:-}" ]; then
		echo "install.sh: could not resolve which release 'latest' points at." >&2
		echo "install.sh: refusing to install -- without a tag there is no checksums.txt to verify against. Retry, or pass an explicit --version vX.Y.Z." >&2
		exit 1
	fi
	VERSION="$resolved"
	echo "install.sh: latest is ${VERSION}."
fi
url="https://github.com/${REPO}/releases/download/${VERSION}/${asset}"
sums_url="https://github.com/${REPO}/releases/download/${VERSION}/checksums.txt"

tmp="$(mktemp)"
sums="$(mktemp)"
trap 'rm -f "$tmp" "$sums"' EXIT
echo "install.sh: downloading tan (${arch_part}-${os_part}, ${VERSION})..."
dl_ok=1
download "$url" "$tmp" || dl_ok=0
if [ "$dl_ok" = "0" ]; then
	echo "install.sh: download failed: ${url}" >&2
	# Only name the musl floor when the requested tag is actually below it --
	# a DNS/proxy/500 failure, or a perfectly valid >=v0.3.0 tag, gets no
	# invented explanation.
	if [ "$os_part" = "unknown-linux-musl" ]; then
		case "$VERSION" in
		v0.0.* | v0.1.* | v0.2.*)
			echo "install.sh: note -- Linux musl assets only exist from v0.3.0 onward; ${VERSION} predates that and has no ${asset} asset." >&2
			;;
		esac
	fi
	exit 1
fi

# ---------------------------------------------------------------------------
# Verify what landed against the checksums.txt published in the SAME release.
#
# TLS says we talked to github.com. It does not say github.com handed us the
# bytes we published, and it says nothing at all about a proxy, a cache, or a
# truncated write. `checksums.txt` is the artefact that does, it already exists
# at every tag, and alp-sdk-vscode already verifies its own managed download
# against it (alplabai/alp-sdk-vscode#389) and refuses a mismatch. Until this
# landed, the two acquisition paths for the same binary disagreed about whether
# they check it -- and the unverified one is the path the extension's
# "Install tan CLI (global)" button runs, whose result the extension's resolver
# then PREFERS over its own verified copy, on every activation, indefinitely.
#
# FOUR distinct outcomes, four distinct messages, all of them refusing. They are
# different facts and a user must not have to guess which one they hit: being
# offline behind a corporate proxy and being handed a tampered binary are not
# the same situation and must not read the same. (#389 reached the same shape
# from the other side.) Nothing is written to the install dir on any of them --
# the binary is still in $tmp here and the trap removes it.
# ---------------------------------------------------------------------------
if command -v sha256sum >/dev/null 2>&1; then
	got="$(sha256sum "$tmp" | cut -d' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
	got="$(shasum -a 256 "$tmp" | cut -d' ' -f1)"
else
	# Outcome 4. Deliberately NOT a warn-and-continue, and deliberately no
	# --no-verify escape hatch: a flag that turns the check off is the hole
	# this closes, wearing a consent form. coreutils, busybox and macOS all
	# ship one of these two, so reaching here means a genuinely unusual host.
	echo "install.sh: cannot verify -- neither sha256sum nor shasum is on PATH." >&2
	echo "install.sh: refusing to install an unverified binary. Install coreutils (sha256sum) or perl/shasum, then re-run." >&2
	exit 1
fi

echo "install.sh: verifying against ${VERSION} checksums.txt..."
if ! download "$sums_url" "$sums" 2>/dev/null; then
	# Outcome 1: the digests could not be fetched. Says nothing about the
	# binary -- which is exactly why it must not be worded like a mismatch.
	echo "install.sh: could not fetch ${sums_url}" >&2
	echo "install.sh: refusing to install -- the binary downloaded, but there is nothing to check it against. This is a fetch failure, NOT evidence the binary is bad. Retry, or check a proxy/firewall." >&2
	exit 1
fi

want="$(awk -v a="$asset" '$2 == a { print $1 }' "$sums" | head -1)"
if [ -z "${want:-}" ]; then
	# Outcome 2: fetched fine, but this asset is not in it. A release that
	# shipped the binary and omitted it from checksums.txt is a release bug,
	# and silently installing anyway is how it would stay one.
	echo "install.sh: ${asset} is not listed in ${VERSION}'s checksums.txt" >&2
	echo "install.sh: refusing to install -- the digest file exists but does not cover this asset, so it cannot be verified. Report this against ${REPO}; the release is incomplete." >&2
	exit 1
fi

if [ "$got" != "$want" ]; then
	# Outcome 3: the one that means something is actually wrong.
	echo "install.sh: SHA256 MISMATCH for ${asset} (${VERSION})" >&2
	echo "install.sh:   expected ${want}" >&2
	echo "install.sh:   got      ${got}" >&2
	echo "install.sh: refusing to install. The downloaded bytes are not the bytes published at ${VERSION} -- corruption, a caching proxy, or tampering. Nothing was written to ${INSTALL_DIR}." >&2
	exit 1
fi
echo "install.sh: sha256 OK (${got})"

chmod +x "$tmp"

dest="${INSTALL_DIR}/tan"
# User-local dir: create + move without sudo. A non-writable dir (e.g. the
# --system /usr/local/bin) needs elevated permission -> use sudo explicitly so
# the admin step is visible, never silent.
if mkdir -p "$INSTALL_DIR" 2>/dev/null && [ -w "$INSTALL_DIR" ]; then
	mv "$tmp" "$dest"
else
	echo "install.sh: ${INSTALL_DIR} needs elevated permission -- running sudo (admin)."
	sudo mkdir -p "$INSTALL_DIR"
	sudo mv "$tmp" "$dest"
	sudo chmod +x "$dest"
fi
# $tmp has been moved to $dest; $sums has not, so clear the trap only after
# removing it by hand -- otherwise a successful install is the one path that
# leaves a temp file behind.
rm -f "$sums"
trap - EXIT

echo "install.sh: installed tan -> ${dest}"
case ":${PATH}:" in
*":${INSTALL_DIR}:"*)
	: # already on PATH -- 'tan' works from any shell
	;;
*)
	if [ "$MODIFY_PATH" = "1" ]; then
		# Pick the login shell's rc file, append the PATH line (idempotent), and
		# announce it -- never edit a dotfile silently. This is what makes a
		# no-sudo user-local install usable globally (notably on macOS, where
		# ~/.local/bin is not on the default PATH).
		case "$(basename "${SHELL:-/bin/sh}")" in
		zsh) rc="$HOME/.zshrc" ;;
		bash)
			if [ "$(uname -s)" = "Darwin" ]; then rc="$HOME/.bash_profile"; else rc="$HOME/.bashrc"; fi
			;;
		*) rc="$HOME/.profile" ;;
		esac
		if [ -f "$rc" ] && grep -qF "$INSTALL_DIR" "$rc" 2>/dev/null; then
			echo "install.sh: ${INSTALL_DIR} already referenced in ${rc} -- not modified."
		else
			printf '\n%s\n' "export PATH=\"${INSTALL_DIR}:\$PATH\"  # added by tan install.sh" >>"$rc"
			echo "install.sh: added ${INSTALL_DIR} to PATH in ${rc}."
			echo "install.sh: open a NEW shell (or run:  . \"${rc}\") to use 'tan' anywhere. Undo: delete that line."
		fi
	else
		echo "install.sh: ${INSTALL_DIR} is not on PATH -- add:  export PATH=\"${INSTALL_DIR}:\$PATH\"  (or re-run without --no-modify-path)"
	fi
	;;
esac
"$dest" --version 2>/dev/null || echo "install.sh: run 'tan --version' to verify (once on PATH)."
