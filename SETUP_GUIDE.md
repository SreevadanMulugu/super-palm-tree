# SuperPalmTree Setup Guide

## Quick Start

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `super-palm-tree`
3. Make it public (for free GitHub Actions)
4. Don't initialize with README (we have one)
5. Click "Create repository"

### 2. Push Code to GitHub

```bash
# Initialize git
cd super-palm-tree
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: SuperPalmTree AI Agent"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/super-palm-tree.git

# Push
git push -u origin main
```

### 3. GitHub Actions Setup

The GitHub Actions workflow is already configured in [`.github/workflows/build.yml`](.github/workflows/build.yml). It will:

- Build **Ubuntu/Debian `.deb`** packages
- Build **Fedora/RHEL/CentOS `.rpm`** packages
- Build **Windows** standalone `.exe`
- Build **macOS** binaries for x64 and ARM64
- Create releases automatically on tags

**No additional setup needed** – it uses free GitHub‑hosted runners!

### 4. Trigger Builds and Create a Release

```bash
# Tag a version
git tag v1.0.0

# Push tag
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build all platform binaries and packages
2. Create a release for the tag
3. Upload all artifacts (.deb, .rpm, .exe, macOS binaries)

You can also push to `main`/`master` or open a pull request to run CI builds without creating a release.

### 5. Download and Install

After the workflow completes, go to:
`https://github.com/YOUR_USERNAME/super-palm-tree/releases`

Download the appropriate binary for your platform.

#### Linux (Ubuntu/Debian) – .deb
```bash
sudo dpkg -i super-palm-tree_1.0.0_amd64.deb
super-palm-tree
```

#### Linux (Fedora/RHEL/CentOS) – .rpm
```bash
sudo dnf install ./super-palm-tree.rpm
# or
sudo rpm -i super-palm-tree.rpm

super-palm-tree
```

#### macOS
```bash
chmod +x super-palm-tree-macos-x64  # or super-palm-tree-macos-arm64
./super-palm-tree-macos-x64
```

#### Windows
```powershell
# Just run the executable
super-palm-tree-windows-x64.exe
```

## Prerequisites

### Required for All Platforms

SuperPalmTree packages are designed to be **zero‑setup**:

- The **Ollama runtime** is bundled inside the application image.
- The **Qwen 3 1.7B GGUF model** is bundled in the package built by GitHub Actions.

On a fresh machine you install the `.deb` / `.rpm` / `.exe` / macOS binary and run `super-palm-tree` – no separate Ollama install is required.  
In local dev builds, if the model file is missing, the app will show in the Web UI that the model is downloading and fetch it automatically.

### Optional: Chrome/Chromium
For browser automation features, install Chrome or Chromium:

**Ubuntu/Debian:**
```bash
sudo apt install chromium-browser
```

**Fedora/RHEL:**
```bash
sudo dnf install chromium
```

**macOS:**
```bash
brew install --cask google-chrome
```

**Windows:**
Download from https://www.google.com/chrome/

## Building Locally

### Prerequisites
- Python 3.11+
- pip

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python src/main.py
```

### Build Standalone Executable
```bash
# Install pyinstaller
pip install pyinstaller

# Build
cd src
pyinstaller --onefile --name super-palm-tree main.py

# Binary will be in src/dist/super-palm-tree
```

### Build RPM Package
```bash
# On Fedora/RHEL/CentOS
sudo dnf install rpm-build rpmdevtools

# Build
make rpm
```

## Project Structure

```
super-palm-tree/
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions CI/CD
├── packaging/
│   └── rpm/
│       └── super-palm-tree.spec    # RPM package spec
├── src/
│   ├── main.py                # Entry point
│   ├── agent.py               # Core agent logic
│   └── browser_tool.py        # Browser automation
├── .gitignore
├── LICENSE
├── Makefile                   # Build automation
├── README.md                  # User documentation
├── requirements.txt           # Python dependencies
└── SETUP_GUIDE.md            # This file
```

## GitHub Actions Details

### Free Tier Limits (What We Use)
- **Linux**: 2,000 minutes/month (Ubuntu runner)
- **Windows**: 2,000 minutes/month (Windows runner)
- **macOS**: 2,000 minutes/month (macOS runner)
- **Storage**: 500MB for packages
- **Bandwidth**: 1GB/month for package downloads

Our workflow uses:
- 4 jobs per build (Linux, Windows, macOS x64, macOS ARM64)
- ~10 minutes per complete build
- ~200 builds/month possible on free tier

### Workflow Triggers
- Push to `main` or `master` branch: builds and tests (no release)
- Pull requests: builds and tests
- Tags starting with `v`: builds packages for all platforms and creates a release

## Using GitHub Tokens Securely

Never paste a raw personal access token (PAT) directly into the workflow file or commit history.

- Use the built‑in `GITHUB_TOKEN` provided by GitHub Actions for most CI tasks (already used in `build.yml`).
- For extra tokens (for example, private package registries), create a **GitHub Secret** in your repository settings and reference it as `${{ secrets.MY_SECRET_NAME }}` in the workflow.
- If you ever accidentally expose a token (for example, in a chat or screenshot), **revoke/rotate it immediately** from the GitHub developer settings page.

## Troubleshooting

### Build Failures

**PyInstaller not found:**
```bash
pip install pyinstaller
```

**RPM build fails:**
```bash
sudo dnf install rpm-build rpmdevtools
rpmdev-setuptree
```

**Ollama connection errors:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Runtime Issues

**Permission denied:**
```bash
chmod +x super-palm-tree
```

**Chrome not found:**
Install Chrome/Chromium or set `CHROME_PATH` environment variable.

**Model not found:**
```bash
ollama pull qwen3:1.7b
```

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create a tag to trigger release
3. ✅ Download and test binaries
4. ✅ Share with users!

## Support

- Issues: https://github.com/YOUR_USERNAME/super-palm-tree/issues
- Discussions: https://github.com/YOUR_USERNAME/super-palm-tree/discussions
