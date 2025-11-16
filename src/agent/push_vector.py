import os
import shutil
import subprocess

# -------------------
# GitHub PAT & 레포지토리
# -------------------
target_repo = os.getenv("TARGET_REPO")  # 예: KNUckle-llm/chatbot
pat = os.getenv("TARGET_REPO_PAT")
branch = os.getenv("TARGET_BRANCH", "14-feature-auto-embedding")

if not target_repo or not pat:
    print("⚠️ target_repo 또는 PAT가 설정되지 않음. push 스킵")
    exit(0)

remote_url = f"https://{pat}@github.com/{target_repo}.git"

# -------------------
# temp 디렉토리 준비
# -------------------
clone_path = "/tmp/target_repo"
if os.path.exists(clone_path):
    shutil.rmtree(clone_path)

print(f"📥 cloning target repo: {remote_url} ...")
subprocess.run(["git", "clone", remote_url, clone_path], check=True)

# Git config (로컬 repo 기준으로 설정)
subprocess.run(["git", "config", "user.email", "github-actions@github.com"], cwd=clone_path)
subprocess.run(["git", "config", "user.name", "GitHub Actions"], cwd=clone_path)

# 브랜치 체크아웃 (없으면 생성)
subprocess.run(["git", "checkout", "-B", branch], cwd=clone_path, check=True)

# -------------------
# chroma_db → clone repo의 지정된 경로로 복사
# -------------------
src_db = "chroma_db"
dst_folder = os.path.join(clone_path, "src/agent/chatbot_20251108")

if os.path.exists(dst_folder):
    shutil.rmtree(dst_folder)
shutil.copytree(src_db, dst_folder)

print(f"📁 DB 복사 완료: {src_db} → {dst_folder}")

# -------------------
# Git add, commit, push
# -------------------
subprocess.run(["git", "add", "."], cwd=clone_path)
commit_result = subprocess.run(
    ["git", "commit", "-m", "Manual push vector DB"],
    cwd=clone_path,
    text=True,
    capture_output=True
)

if "nothing to commit" in commit_result.stdout:
    print("변경 사항 없음 → push 생략")
    exit(0)

push_result = subprocess.run(
    ["git", "push", "origin", branch],
    cwd=clone_path,
    text=True,
    capture_output=True
)

if push_result.returncode != 0:
    print("Push 실패:")
    print(push_result.stderr)
    exit(1)

print(f"✅ push 완료! → {target_repo}:{branch}")