Name:           superpalmtree
Version:        %{version}
Release:        1%{?dist}
Summary:        AI-powered browser automation agent
License:        MIT
URL:            https://github.com/%{github_user}/super-palm-tree
Source0:        superpalmtree

BuildArch:      x86_64

%description
SuperPalmTree is an AI-powered browser automation agent that uses local LLMs
for intelligent web interaction. It features autonomous browsing, task execution,
and multi-step workflow automation.

%prep
# No prep needed for binary distribution

%build
# Binary is pre-built

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 %{SOURCE0} %{buildroot}/usr/bin/superpalmtree

%files
/usr/bin/superpalmtree

%changelog
* Sun Feb 01 2025 SuperPalmTree Team <team@superpalmtree.dev> - 1.0.0-1
- Initial RPM release
