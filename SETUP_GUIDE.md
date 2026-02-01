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

- Build for Linux (x64 + RPM package)
- Build for Windows (x64)
- Build for macOS (x64 and ARM64)
- Create releases automatically on tags

**No additional setup needed** - it uses free GitHub-hosted runners!

### 4. Create a Release

```bash
# Tag a version
git tag v1.0.0

# Push tag
git push origin v1.0.0
```

GitHub Actions will automatically:
1. Build all binaries
2. Create a release
3. Upload all artifacts

### 5. Download and Install

After the workflow completes, go to:
`https://github.com/YOUR_USERNAME/super-palm-tree/releases`

Download the appropriate binary for your platform.

#### Linux (Fedora/RHEL/CentOS)
```bash
sudo dnf install ./super-palm-tree.rpm
# or
sudo rpm -i super-palm-tree.rpm

super-palm-tree
```

#### Linux (Generic)
```bash
chmod +x super-palm-tree-linux-x64
./super-palm-tree-linux-x64
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
- **Ollama**: Install from https://ollama.ai

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull qwen3:1.7b
```

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
- Push to `main` or `master` branch: Builds and tests
- Pull requests: Builds and tests
- Tags starting with `v`: Builds and creates release

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
