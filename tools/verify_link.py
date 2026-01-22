import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_link():
    """
    Minimal script to verify that the CData MCP server is responding.
    This satisfies Phase 2: Link (Verification).
    """
    username = os.getenv("CDATA_USERNAME")
    password = os.getenv("CDATA_PASSWORD")
    url = os.getenv("CDATA_MCP_URL", "https://mcp.cloud.cdata.com/mcp")

    if not username or not password:
        print("❌ Error: CDATA_USERNAME or CDATA_PASSWORD not found in .env")
        return False

    print(f"🔗 Attempting handshake with {url}...")
    
    # MCP Handshake (Example based on standard MCP over HTTP)
    # Note: Using Basic Auth as per implementation plan
    try:
        # Most MCP servers over HTTP respond to a 'listTools' type request or simple GET
        # For CData Connect AI MCP specifically, we follow the pattern in the plan
        response = requests.post(
            url,
            auth=(username, password),
            json={"method": "listTools", "params": {}},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Handshake Successful! CData MCP is responding.")
            tools = response.json().get("result", {}).get("tools", [])
            print(f"🛠️ Available Tools: {[t['name'] for t in tools]}")
            return True
        else:
            print(f"❌ Handshake Failed. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        return False

if __name__ == "__main__":
    verify_link()
