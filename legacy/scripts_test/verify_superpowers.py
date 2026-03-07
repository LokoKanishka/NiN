#!/usr/bin/env python3
"""
verify_superpowers.py
This script acts as a self-diagnostic tool for the AI.
It verifies the presence of configured MCP servers and essential tool binaries (like npx, docker, etc.).
"""

import os
import json
import subprocess

MCP_CONFIG = "/home/lucy-ubuntu/.gemini/antigravity/mcp_config.json"

def check_binary(binary_name):
    try:
        subprocess.run(["which", binary_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def verify_mcp_config():
    print("--- 🦸‍♂️ Antigravity Superpower Diagnostics ---")
    if not os.path.exists(MCP_CONFIG):
        print("❌ [MCP] Config file not found!")
        return
    
    with open(MCP_CONFIG, 'r') as f:
        data = json.load(f)
    
    servers = data.get("mcpServers", {})
    print(f"📦 Found {len(servers)} MCP servers configured:")
    for name, config in servers.items():
        cmd = config.get("command")
        has_cmd = check_binary(cmd)
        status = "✅" if has_cmd else "❌ (Binary missing)"
        print(f"  - [{status}] {name} (Command: {cmd})")

def verify_native_tools():
    print("\n🛠️ Verifying Native Environment Tools:")
    tools = ["python3", "npx", "docker", "git", "grep", "curl"]
    for tool in tools:
        status = "✅" if check_binary(tool) else "❌"
        print(f"  - [{status}] {tool}")

if __name__ == "__main__":
    verify_mcp_config()
    verify_native_tools()
    print("\n💡 AI Reminder: You have access to browser_subagent, search_web, generate_image, multi_replace_file_content natively.")
