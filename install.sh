#!/bin/bash

# Create a virtual environment
python3 -m venv ~/.bedrock-cli-venv

# Activate the virtual environment
source ~/.bedrock-cli-venv/bin/activate

# Install the package
pip install -e .

# Create an alias for the bedrock command
echo 'alias bedrock="~/.bedrock-cli-venv/bin/bedrock"' >> ~/.bashrc
echo 'alias bedrock="~/.bedrock-cli-venv/bin/bedrock"' >> ~/.zshrc

echo "Installation complete. Please restart your terminal or run 'source ~/.bashrc' (or ~/.zshrc) to use the 'bedrock' command."