# SuperPalmTree 🤖

[![Build Status](https://github.com/YOUR_USERNAME/super-palm-tree/workflows/Build%20and%20Release/badge.svg)](https://github.com/YOUR_USERNAME/super-palm-tree/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SuperPalmTree is an AI-powered browser automation agent that uses local LLMs for intelligent web interaction. It features autonomous browsing, task execution, and multi-step workflow automation.

## Features

- 🧠 **Local AI**: Runs entirely on your machine using local LLMs (Ollama)
- 🔒 **Privacy First**: No data sent to external APIs
- 🌐 **Browser Automation**: Built-in browser control via CDP (Chrome DevTools Protocol)
- 📝 **Task Planning**: Intelligent task breakdown and execution
- 🖥️ **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Download Pre-built Binaries (Recommended)

Download the latest release for your platform from the [Releases](https://github.com/YOUR_USERNAME/super-palm-tree/releases) page.  
GitHub Actions builds **all platforms automatically** whenever you push a `v*` tag.

#### Linux – Ubuntu/Debian (.deb)
```bash
# Download and install .deb
sudo dpkg -i super-palm-tree_1.0.0_amd64.deb

# Run
super-palm-tree
```

#### Linux – Fedora/RHEL/CentOS (.rpm)
```bash
# Download and install .rpm
sudo dnf install ./super-palm-tree-1.0.0-1.x86_64.rpm
# or
sudo rpm -i super-palm-tree-1.0.0-1.x86_64.rpm

# Run
super-palm-tree
```

#### Linux (Generic)
```bash
# Download binary
chmod +x super-palm-tree-linux-x64
./super-palm-tree-linux-x64
```

#### macOS
```bash
# Intel Macs
chmod +x super-palm-tree-macos-x64
./super-palm-tree-macos-x64

# Apple Silicon Macs
chmod +x super-palm-tree-macos-arm64
./super-palm-tree-macos-arm64
```

#### Windows
```powershell
# Download and run
super-palm-tree-windows-x64.exe
```
## Zero-Setup Design (Bundled Ollama + Model)

SuperPalmTree is designed to **just work on a fresh machine**:

- A platform-specific **Ollama binary is bundled** inside the app.
- A quantized **Qwen 3 1.7B GGUF model** is bundled into the package.
- The first time you run the app, it **starts the embedded Ollama server** and **prepares the local model** automatically.
- When building from source in development, if the model file is missing, the app will **show a status message that the model is downloading** and fetch it for you.

You do **not** need to pre-install Ollama or manually pull models on the target system. The GitHub Actions builds and the one-file binaries are responsible for shipping everything.

For browser automation features, you still need Chrome/Chromium installed on the system.

### Build from Source

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/super-palm-tree.git
cd super-palm-tree

# Install dependencies
pip install -r requirements.txt

# Run directly
python src/main.py

# Or build standalone executable
pyinstaller --onefile --name super-palm-tree src/main.py
```

## Usage

### Interactive Mode
```bash
super-palm-tree
```

### Single Task Mode
```bash
super-palm-tree "Go to example.com and find the contact email"
```

### Configuration

Create a `.env` file in your working directory:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen3:1.7b
CHROME_PATH=/usr/bin/google-chrome
```

## Development

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Lint code
flake8 src
black src
```

## Project Structure

```
super-palm-tree/
├── src/                    # Source code
│   ├── main.py            # Entry point
│   ├── agent.py           # Core agent logic
│   └── browser_tool.py    # Browser automation
├── packaging/             # Packaging files
│   └── rpm/              # RPM spec files
├── .github/              # GitHub Actions
│   └── workflows/
├── requirements.txt      # Dependencies
└── README.md
```

## Building Packages

### RPM Package (Fedora/RHEL)
```bash
# Install build tools
sudo dnf install rpm-build rpmdevtools

# Setup build directory
rpmdev-setuptree

# Build RPM
cp packaging/rpm/super-palm-tree.spec ~/rpmbuild/SPECS/
cp dist/super-palm-tree-linux-x64 ~/rpmbuild/SOURCES/
rpmbuild -bb ~/rpmbuild/SPECS/super-palm-tree.spec
```

### Standalone Executable
```bash
# Using PyInstaller
pyinstaller --onefile --name super-palm-tree src/main.py
```

## GitHub Actions

This project uses GitHub Actions to automatically build and release binaries and packages for:
- **Ubuntu/Debian**: `.deb` package
- **Fedora/RHEL/CentOS**: `.rpm` package
- **Windows**: standalone `super-palm-tree-windows-x64.exe`
- **macOS**: standalone `super-palm-tree-macos-x64` and `super-palm-tree-macos-arm64`

To create a new release:
1. Push a tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions will run on GitHub’s runners, build all artifacts, and publish them on the **Releases** page.

You can also push to `main`/`master` or open a pull request to trigger CI builds without creating a release.

## Customizing SuperPalmTree

You can freely modify and extend the agent:

- Core entrypoint and web UI server: `src/main.py`
- Planning + execution agent logic: `src/agent.py`
- Browser automation (Chromium + CDP): `src/browser_tool.py`
- Frontend UI (black & white chat interface): `static/index.html` + `static/app.js`

Typical developer loop:

```bash
git clone https://github.com/YOUR_USERNAME/super-palm-tree.git
cd super-palm-tree
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run in dev mode
python src/main.py

# Build a single-file binary for your platform
pyinstaller --onefile --name super-palm-tree src/main.py
```

After you commit your changes and push a new `v*` tag, GitHub Actions will build new cross‑OS artifacts with your modifications.

## Why you will see updates

The code is intentionally updated over time to:

- Ship **bug fixes and security hardening**
- Improve **model quality and performance**
- Refine **packaging and zero‑setup behavior** across different OSes

All updates are versioned (for example `v1.0.1`, `v1.1.0`), and you can choose when to install newer releases.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Ollama](https://ollama.ai) for local LLM inference
- Browser automation via Chrome DevTools Protocol
- Inspired by the need for privacy-preserving AI automation
