import os
import shutil
import subprocess

# -------------------
# GitHub PAT & 레포지토리
# -------------------
target_repo = os.getenv("TARGET_REPO")        # 예: KNUckle-llm/chatbot
pat = os.getenv("TARGET_REPO_PAT")
branch = os.getenv("TARGET_BRANCH", "14-feature-auto-embedding")

if not target_repo or not pat:
    print("⚠️ target_repo 또는 PAT가 설정되지 않음. push 스킵")
    exit(0)

# -------------------
# Clone target repo
# -------------------
remote_url = f"https://{pat}@github.com/{target_repo}.git"
clone_path = "/tmp/target_repo"

if os.path.exists(clone_path):
    shutil.rmtree(clone_path)

print(f"📥 cloning target repo: {remote_url} ...")
subprocess.run(["git", "clone", "-b", branch, remote_url, clone_path], check=True)

# -------------------
# A repo → B repo로 DB 복사
# -------------------
src_db = "chroma_db"  # A 계정 repo 내부
dst_folder = os.path.join(clone_path, "src/agent/chatbot_20251108")  # B repo 내부

# 기존 폴더 삭제 후 복사
if os.path.exists(dst_folder):
    shutil.rmtree(dst_folder)

shutil.copytree(src_db, dst_folder)
print(f"📁 DB 복사 완료: {src_db} → {dst_folder}")

# -------------------
# B repo에서 commit & push
# -------------------
subprocess.run(["git", "-C", clone_path, "add", "."], check=True)
subprocess.run(["git", "-C", clone_path, "commit", "-m", "Update vector DB"], check=False)
subprocess.run(["git", "-C", clone_path, "push", "origin", branch], check=True)

print(f"✅ {src_db} → {target_repo}:{branch} push 완료!")
