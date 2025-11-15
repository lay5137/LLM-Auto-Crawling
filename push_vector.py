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
# Git Config
# -------------------
subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"])
subprocess.run(["git", "config", "--global", "user.name", "github-actions"])

# -------------------
# chroma_db → src/agent/chatbot_20251108로 복사
# -------------------
src_db = "chroma_db"
dst_folder = "src/agent/chatbot_20251108"

# 기존 폴더 삭제 후 복사
if os.path.exists(dst_folder):
    shutil.rmtree(dst_folder)
shutil.copytree(src_db, dst_folder)

# -------------------
# Git add, commit, push
# -------------------
subprocess.run(["git", "add", dst_folder])
subprocess.run(["git", "commit", "-m", "Manual push vector DB"], check=False)
subprocess.run(["git", "push", remote_url, f"HEAD:{branch}"])

print(f"✅ {src_db} → {target_repo}:{dst_folder} ({branch}) push 완료!")
