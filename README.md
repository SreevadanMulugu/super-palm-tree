# AgentSmith 🤖

[![Build Status](https://github.com/YOUR_USERNAME/agentsmith/workflows/Build%20and%20Release/badge.svg)](https://github.com/YOUR_USERNAME/agentsmith/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AgentSmith is an AI-powered browser automation agent that uses local LLMs for intelligent web interaction. It features autonomous browsing, task execution, and multi-step workflow automation.

## Features

- 🧠 **Local AI**: Runs entirely on your machine using local LLMs (Ollama)
- 🔒 **Privacy First**: No data sent to external APIs
- 🌐 **Browser Automation**: Built-in browser control via CDP (Chrome DevTools Protocol)
- 📝 **Task Planning**: Intelligent task breakdown and execution
- 🖥️ **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Download Pre-built Binaries

Download the latest release for your platform from the [Releases](https://github.com/YOUR_USERNAME/agentsmith/releases) page.

#### Linux (Fedora/RHEL/CentOS)
```bash
# Download and install RPM
sudo dnf install ./agentsmith.rpm
# or
sudo rpm -i agentsmith.rpm

# Run
agentsmith
```

#### Linux (Generic)
```bash
# Download binary
chmod +x agentsmith-linux-x64
./agentsmith-linux-x64
```

#### macOS
```bash
# Intel Macs
chmod +x agentsmith-macos-x64
./agentsmith-macos-x64

# Apple Silicon Macs
chmod +x agentsmith-macos-arm64
./agentsmith-macos-arm64
```

#### Windows
```powershell
# Download and run
agentsmith-windows-x64.exe
```

### Build from Source

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/agentsmith.git
cd agentsmith

# Install dependencies
pip install -r requirements.txt

# Run directly
python src/main.py

# Or build standalone executable
pyinstaller --onefile --name agentsmith src/main.py
```

## Prerequisites

- **Ollama**: Install from [ollama.ai](https://ollama.ai)
- **Chrome/Chromium**: For browser automation

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull required model
ollama pull qwen3:1.7b
```

## Usage

### Interactive Mode
```bash
agentsmith
```

### Single Task Mode
```bash
agentsmith "Go to example.com and find the contact email"
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
agentsmith/
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
cp packaging/rpm/agentsmith.spec ~/rpmbuild/SPECS/
cp dist/agentsmith-linux-x64 ~/rpmbuild/SOURCES/
rpmbuild -bb ~/rpmbuild/SPECS/agentsmith.spec
```

### Standalone Executable
```bash
# Using PyInstaller
pyinstaller --onefile --name agentsmith src/main.py
```

## GitHub Actions

This project uses GitHub Actions to automatically build and release binaries for:
- Linux (x64 + RPM package)
- Windows (x64)
- macOS (x64 and ARM64)

To create a new release:
1. Push a tag: `git tag v1.0.0 && git push origin v1.0.0`
2. GitHub Actions will build and publish automatically

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
