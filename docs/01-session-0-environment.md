# Session 0 — Development Environment

**Effort:** 3–5 hours (one-time setup)
**Goal:** A reliable Linux-on-Windows dev environment with every tool we'll need for both projects.

## Why WSL2 (not devcontainer, not native Windows)

We tried devcontainers in Windsurf — its built-in extension is buggy and can't parse `devcontainer.json`. Native Windows install is painful because most tools are Linux-first. **WSL2 is the path of least friction**, and what most professional Windows-based devs use.

## Architecture

```
Windows 11
├── Docker Desktop (with WSL2 backend)
├── Windsurf IDE
│   └── WSL extension (built-in, works fine)
│       └── connects to ↓
└── WSL2: Ubuntu 24.04
    ├── uv (Python toolchain)
    ├── mise (CLI tool version manager)
    │   └── manages: kubectl, helm, k9s, kind, jq, yq, kustomize
    ├── pre-commit
    ├── direnv
    └── /home/<user>/projects/Real-World-ML-Project-rebuild  ← work here
```

## Step-by-step

### Step 1 — Install WSL2 + Ubuntu

In **PowerShell as Administrator**:

```powershell
wsl --install -d Ubuntu-24.04
```

Reboot if asked. On first launch, Ubuntu prompts for a Linux username and password. Write the password down.

Verify:

```bash
uname -a
cat /etc/os-release
```

### Step 2 — Update Ubuntu packages

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl git unzip ca-certificates
```

### Step 3 — Configure Docker Desktop ↔ WSL2 integration

1. Open Docker Desktop on Windows.
2. **Settings → Resources → WSL Integration**
3. Enable integration with **Ubuntu-24.04**.
4. Apply & Restart.

Verify in Ubuntu:

```bash
docker version
docker run --rm hello-world
```

### Step 4 — Install `uv` (Python toolchain)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version
```

### Step 5 — Install `mise` (CLI tool version manager)

```bash
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
source ~/.bashrc
mise --version
```

### Step 6 — Clone the rebuild repo into WSL filesystem

**IMPORTANT:** Clone into the Linux home dir, not `/mnt/c/...`. Performance is 10x faster.

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/Bhujith10/Real-World-ML-Project-rebuild.git
cd Real-World-ML-Project-rebuild
```

Configure git inside WSL:

```bash
git config --global user.name "Bhujith10"
git config --global user.email "<your-github-email>"
```

### Step 7 — Use `mise` to install the K8s toolchain

The project's `mise.toml` pins exact versions. Trust the file, then install:

```bash
mise trust
mise install
```

This installs: `kubectl`, `helm`, `k9s`, `jq`, `yq`, `kustomize` (and `gh` if listed).

We also need `kind`. Add it to `mise.toml` if not already present, then re-run `mise install`. Or install manually:

```bash
[ -z "$(command -v kind)" ] && \
  curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64 && \
  chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
kind --version
```

### Step 8 — Install `pre-commit` and `direnv`

```bash
uv tool install pre-commit
sudo apt install -y direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
source ~/.bashrc
```

### Step 9 — Verify everything works

```bash
docker --version
uv --version
mise --version
kubectl version --client
helm version
k9s version
kind --version
jq --version
yq --version
kustomize version
pre-commit --version
direnv --version
psql --version || sudo apt install -y postgresql-client
```

All commands should return version strings without errors.

### Step 10 — Open the project in Windsurf via WSL

1. In Windsurf, click the bottom-left `><` icon
2. Select **"Connect to WSL"**
3. Once connected, **Open Folder** → `/home/<your-user>/projects/Real-World-ML-Project-rebuild`
4. Confirm the bottom-left now says "WSL: Ubuntu-24.04"
5. Open a terminal — it's bash, inside WSL

You're done with Session 0.

## Common issues & fixes

| Problem | Fix |
|---|---|
| `wsl --install` says "command not found" | Update Windows to a recent version (Win 11 or 10 build 19044+) |
| `0x80370102` virtualization error | Enable Intel VT-x / AMD-V in BIOS |
| Docker commands hang in WSL | Restart Docker Desktop; verify WSL integration is on |
| `mise install` fails on a tool | Run `mise install <tool>` individually for clearer errors |
| WSL eats RAM | Create `C:\Users\<you>\.wslconfig` with `[wsl2]\nmemory=8GB\nswap=2GB` |
| Slow file I/O | Don't keep project at `/mnt/c/...`; clone into `~/projects/` |

## End-of-session commit

```bash
cd ~/projects/Real-World-ML-Project-rebuild
git add docs/
git commit -m "session 0: add complete plan as docs/"
git push
```
