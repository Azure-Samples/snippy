# Snippy Functions – Dev Container image
FROM mcr.microsoft.com/vscode/devcontainers/universal:latest

# ──────────────────────────────────────────────────────────────
# 1 – First‑run welcome notice
COPY first-run-notice.txt /tmp/staging/
RUN sudo mv -f /tmp/staging/first-run-notice.txt \
        /usr/local/etc/vscode-dev-containers/ \
    && sudo rm -rf /tmp/staging

# ──────────────────────────────────────────────────────────────
# 2 – PowerShell 7.x
RUN sudo apt-get update \
 && sudo apt-get install -y wget apt-transport-https software-properties-common \
 && wget -q https://packages.microsoft.com/config/ubuntu/$(. /etc/os-release && echo $VERSION_ID)/packages-microsoft-prod.deb \
 && sudo dpkg -i packages-microsoft-prod.deb \
 && sudo apt-get update \
 && sudo apt-get install -y powershell \
 && sudo apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# ──────────────────────────────────────────────────────────────
# 3 – Azure Functions Core Tools v4
# Using npm ensures the latest build and works on any distro.
RUN npm install -g azure-functions-core-tools@4 --unsafe-perm

# ──────────────────────────────────────────────────────────────
# 4 – Azure Developer CLI
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

# ──────────────────────────────────────────────────────────────
# 5 – Mechanical‑Markdown (quick‑start doc validation)
RUN pip install --no-cache-dir mechanical-markdown
