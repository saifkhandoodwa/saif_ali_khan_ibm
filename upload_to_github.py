"""
Automated GitHub Repository Setup & Push Utility.
Helps initialize Git, commit all project files, and push to GitHub.
"""

import os
import subprocess
import sys


def run_cmd(cmd, check=True):
    print(f">> {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr and res.returncode != 0:
        print(f"Error: {res.stderr.strip()}", file=sys.stderr)
    if check and res.returncode != 0:
        sys.exit(res.returncode)
    return res


def main():
    print("==================================================")
    print("🚀 GITHUB REPOSITORY UPLOAD HELPER")
    print("==================================================")

    # 1. Check Git installed
    git_check = run_cmd("git --version", check=False)
    if git_check.returncode != 0:
        print("[-] Git is not installed or not found in PATH.")
        print("Please install Git from https://git-scm.com/downloads and rerun.")
        return

    # 2. Check Git user config
    name_check = run_cmd("git config user.name", check=False)
    if not name_check.stdout.strip():
        user_name = input("Enter your Name for Git commits (e.g. John Doe): ").strip()
        if user_name:
            run_cmd(f'git config user.name "{user_name}"')

    email_check = run_cmd("git config user.email", check=False)
    if not email_check.stdout.strip():
        user_email = input("Enter your Email for Git commits (e.g. you@example.com): ").strip()
        if user_email:
            run_cmd(f'git config user.email "{user_email}"')

    # 3. Initialize Git if needed
    if not os.path.exists(".git"):
        print("[*] Initializing local Git repository...")
        run_cmd("git init")
        run_cmd("git branch -M main")
    else:
        print("[*] Local Git repository already initialized.")

    # 4. Stage and commit
    print("[*] Staging files...")
    run_cmd("git add .")
    
    status = run_cmd("git status --porcelain", check=False)
    if status.stdout.strip():
        print("[*] Creating initial commit...")
        run_cmd('git commit -m "feat: AI smart traffic light controller & visual simulation"')
    else:
        print("[*] Working tree clean, nothing new to commit.")

    # 5. Remote repository setup
    remote_check = run_cmd("git remote get-url origin", check=False)
    repo_url = ""
    if remote_check.returncode == 0:
        repo_url = remote_check.stdout.strip()
        print(f"[*] Current remote origin: {repo_url}")
    else:
        print("\n--------------------------------------------------")
        print("Step: Link to your GitHub Repository")
        print("1. Go to https://github.com/new and create a new repository (e.g. ai-traffic-light).")
        print("2. Copy the repository URL.")
        print("--------------------------------------------------")
        repo_url = input("Paste your GitHub repository URL: ").strip()
        if repo_url:
            run_cmd(f"git remote add origin {repo_url}")

    if repo_url:
        print(f"\n[*] Pushing to {repo_url} on branch 'main'...")
        push_res = run_cmd("git push -u origin main", check=False)
        if push_res.returncode == 0:
            print("\n🎉 SUCCESS! Your AI Traffic Light project is live on GitHub!")
        else:
            print("\n[!] Push incomplete. If prompted for credentials, please sign in or use a GitHub Personal Access Token.")
            print(f"You can also run manually:\n  git push -u origin main")
    else:
        print("\n[*] Remote URL was not provided. You can push anytime later using:")
        print("  git remote add origin <YOUR_GITHUB_REPO_URL>")
        print("  git push -u origin main")


if __name__ == "__main__":
    main()
