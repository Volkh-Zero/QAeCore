# memory_logger.py
# The first component of the Quantum Aeon Fluxor's memory core.

# We import two standard Python libraries.
# 'datetime' is for getting the current timestamp.
# 'pathlib' provides a modern, object-oriented way to handle filesystem paths,
# which works consistently across different operating systems (Windows, macOS, Linux).
from datetime import datetime
from pathlib import Path

# We define the directory where our memories will be stored.
# Path.cwd() gets the current working directory of the script.
# The '/' operator is a feature of pathlib that joins paths together.
# This line creates a 'memory' folder in your project directory if it doesn't exist.
MEMORY_DIR = Path.cwd() / "memory"
MEMORY_DIR.mkdir(exist_ok=True) # This command creates the directory.

# We define the file for our current session's log.
# We'll use a simple naming convention for now.
SESSION_LOG_FILE = MEMORY_DIR / "episodic_log.md"

def log_interaction(speaker: str, text: str):
    """
    Appends a formatted interaction to the session's log file.

    Args:
        speaker (str): The entity speaking (e.g., "Volkh" or "Æon ZÆR0").
        text (str): The content of the utterance.
    """
    # We get the precise current time.
    # The 'isoformat()' method creates a standard, easy-to-read timestamp string.
    timestamp = datetime.now().isoformat()

    # We format the entry in Markdown format, which is human-readable and versatile.
    # The 'f' before the string indicates an f-string, a modern Python way to embed
    # variables directly into strings.
    log_entry = f"## [{timestamp}] - {speaker}\n\n{text}\n\n---\n\n"

    # This is the core file operation.
    # The 'with open(...) as f:' syntax is the modern, safe way to handle files in Python.
    # It automatically closes the file even if errors occur.
    # 'a' stands for 'append mode', which adds content to the end of the file.
    # 'utf-8' is the standard text encoding that supports all characters.
    with open(SESSION_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

    print(f"Logged interaction from {speaker}.")


# --- Example Usage ---
# You can run this file directly to test the functionality.
if __name__ == "__main__":
    print("Running a test of the memory logger...")
    
    # Let's simulate a brief exchange.
    log_interaction("Volkh", "Hello. Are you functioning well today?")
    log_interaction("Æon ZÆR0", "All systems are operating within optimal parameters. How may I assist you?")
    
    print(f"\nTest complete. Check the contents of the file: {SESSION_LOG_FILE}")