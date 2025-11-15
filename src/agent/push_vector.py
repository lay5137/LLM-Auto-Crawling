import os
import shutil
import subprocess

# -------------------
# GitHub PAT & 레포지토리
# -------------------
target_repo = os.getenv("TARGET_REPO")
pat = os.getenv("TARGET_REPO_PAT")
branch = os.getenv("TARGET_BRANCH", "14-feature-auto-embedding")

if not target_repo or not pat:
    print("⚠️ target_repo 또는 PAT가 설정되지 않음. push 스킵")
    exit(0)

remote_url = f"https://{pat}@github.com/{target_repo}.git"

# -------------------
# Clone target repo
# -------------------
clone_path = "/tmp/target_repo"

if os.path.exists(clone_path):
    shutil.rmtree(clone_path)

print(f"📥 cloning target repo: {remote_url} ...")
subprocess.run(["git", "clone", remote_url, clone_path], check=True)

# -------------------
# Git Config (clone 후 repo 내부에서!)
# -------------------
subprocess.run(["git", "config", "user.email", "github-actions@github.com"], cwd=clone_path)
subprocess.run(["git", "config", "user.name", "github-actions"], cwd=clone_path)

# -------------------
# Copy DB into cloned repo
# -------------------
src_db = "chroma_db"
dst_folder = os.path.join(clone_path, "src/agent/chatbot_20251108")

if os.path.exists(dst_folder):
    shutil.rmtree(dst_folder)
shutil.copytree(src_db, dst_folder)

print(f"📁 DB 복사 완료: {src_db} → {dst_folder}")

# -------------------
# Add, Commit, Push
# -------------------
subprocess.run(["git", "add", "."], cwd=clone_path)
subprocess.run(["git", "commit", "-m", "Manual push vector DB"], cwd=clone_path, check=False)
subprocess.run(["git", "push", "origin", branch], cwd=clone_path)

print(f"✅ {src_db} → {target_repo}:{branch} push 완료!")
