import os
import subprocess
from datetime import datetime
from pathlib import Path


def commit_and_push():
    print("committing and pushing data folder to github")

    # Define repo path (assuming script runs inside the cloned repo)
    REPO_PATH = Path(__file__).parent.absolute()
    print(REPO_PATH)

    # File to update (adjust as needed)
    FILE_TO_UPDATE = REPO_PATH.joinpath("data")
    print(FILE_TO_UPDATE)

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
    commit_and_push()
    pass
