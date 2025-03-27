import os
import subprocess
from datetime import datetime
from pathlib import Path

# Define repo path (assuming script runs inside the cloned repo)
REPO_PATH = Path(__file__).parent.absolute()

print(REPO_PATH)

# File to update (adjust as needed)
FILE_TO_UPDATE = REPO_PATH.joinpath("data/test.json")

print(FILE_TO_UPDATE)

def update_content():
    """Modify the file with new data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    content = f"# My GitHub Pages Site\n\nUpdated on: {timestamp}"
    
    if os.path.exists(FILE_TO_UPDATE):
        with open(FILE_TO_UPDATE, "a") as f:
            f.write(content)
    else:
        with open(FILE_TO_UPDATE, "x") as f:
            f.write(content)

def commit_and_push():
    """Commit and push changes."""
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"], check=True)
        subprocess.run(["git", "add", FILE_TO_UPDATE], check=True)
        subprocess.run(["git", "commit", "-m", "Automated update"], check=True)
        subprocess.run(["git", "push"], check=True)
    except subprocess.CalledProcessError:
        print("No changes to commit.")

if __name__ == "__main__":
    update_content()
    commit_and_push()
    pass
