#!/usr/bin/env bash
set -euo pipefail

echo "[post-create] Updating apt packages..."
# Install base OS packages needed for scanners and build tools
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  curl ca-certificates gnupg lsb-release jq bash-completion \
  g++ make git pkg-config libssl-dev

# Install Python deps (root workspace + web_ui) inside devcontainer venv/ default env
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
if [ -f web_ui/requirements.txt ]; then
  pip install -r web_ui/requirements.txt
fi

# Install Syft
if ! command -v syft >/dev/null 2>&1; then
  echo "[post-create] Installing Syft..."
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sudo sh -s -- -b /usr/local/bin
fi
# Install Grype
if ! command -v grype >/dev/null 2>&1; then
  echo "[post-create] Installing Grype..."
  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin
fi
# Install Trivy (optional)
if ! command -v trivy >/dev/null 2>&1; then
  echo "[post-create] Installing Trivy..."
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin
fi

# Enable Docker group usage (docker-outside-of-docker feature already sets this mostly)
if getent group docker >/dev/null 2>&1; then
  sudo usermod -aG docker $(whoami) || true
fi

# Create a convenience run script for web UI
sudo tee /usr/local/bin/run-web-ui >/dev/null <<'EOF'
#!/usr/bin/env bash
python web_ui/app.py
EOF
sudo chmod +x /usr/local/bin/run-web-ui

# Print versions
python --version
pip freeze | grep -E 'Flask|requests|packaging' || true
syft version || true
grype version || true
trivy --version || true

echo "[post-create] Done."
