import subprocess
import time

def main():
    # Start puppeteer server directly
    print("Starting puppeteer server directly...")
    process = subprocess.Popen(
        ["C:/Users/UMINDA/AppData/Roaming/npm/mcp-server-puppeteer.cmd"],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

    # Wait for server to start
    time.sleep(5)

    # Wait for user input
    print("\nPuppeteer MCP server is running in a separate console window.")
    print("You can now use the puppeteer MCP server.")
    print("Press Enter to stop the server...")
    input()

    # Stop server
    print("Stopping puppeteer server...")
    process.terminate()
    print("Puppeteer server terminated")

if __name__ == "__main__":
    main()
