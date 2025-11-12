# =============================================
# 📘 TXT → Chroma 벡터 DB 저장 (날짜 기반 + GitHub 자동 푸시)
# =============================================
import os
import re
import shutil
import unicodedata
import pandas as pd
from datetime import datetime
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_chroma import Chroma
import subprocess

# =============================================
# 📌 경로 설정
# =============================================
docs_folder = "./result_txt"
metadata_file = "./result_files/metadata.xlsx"

# 📌 오늘 날짜 기반 DB 이름 (YYYY-MM-DD)
today_str = datetime.now().strftime("%Y-%m-%d")
db_path = os.path.join("./chroma_db", today_str)

# 기존 DB 삭제 (같은 날짜 DB만)
if os.path.exists(db_path):
    shutil.rmtree(db_path)
    print(f"🗑️ 기존 DB 삭제 완료: {db_path}")

os.makedirs(db_path, exist_ok=True)
print(f"📁 새 DB 생성: {db_path}")

# =============================================
# 📌 텍스트 분할
# =============================================
text_splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separator="\n"
)

# =============================================
# 📌 임베딩 모델
# =============================================
hf_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

# =============================================
# 📌 Chroma DB
# =============================================
db = Chroma(persist_directory=db_path, embedding_function=hf_embeddings)

# =============================================
# 📌 파일명 변환
# =============================================
def safe_search_key(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.replace(" ", "_")
    return name

# =============================================
# 📌 메타데이터 로드
# =============================================
metadata_df = pd.read_excel(metadata_file)
metadata_dict = {}
for _, row in metadata_df.iterrows():
    orig = unicodedata.normalize('NFC', str(row["게시글 제목"]).strip())
    meta = {
        "file_name": orig,
        "department": str(row.get("관련부서", "") or "").strip(),
        "url": str(row.get("URL", "") or "").strip(),
        "date": str(row.get("작성일", "") or "").strip()
    }
    metadata_dict[orig] = meta
    metadata_dict[safe_search_key(orig)] = meta

# =============================================
# 📌 TXT 로드 및 DB 추가
# =============================================
file_count = 0
for filename in os.listdir(docs_folder):
    if not filename.endswith(".txt"):
        continue

    # 🟡 최대 3개 문서만 임베딩 (테스트용)
    if file_count >= 3:
        print("⏹️ 3개 문서까지만 임베딩 진행 (테스트용)")
        break

    base_name = unicodedata.normalize('NFC', os.path.splitext(filename)[0].strip())
    safe_key_name = safe_search_key(base_name)

    meta = metadata_dict.get(base_name) or metadata_dict.get(safe_key_name)
    if meta is None:
        print(f"⚠️ {filename} 메타데이터 없음 → 건너뜀")
        continue

    try:
        loader = TextLoader(os.path.join(docs_folder, filename), encoding="utf-8")
        documents = loader.load_and_split(text_splitter=text_splitter)
        for doc in documents:
            doc.metadata.update(meta)

        db.add_documents(documents)
        file_count += 1

        print(f"✅ {filename} 추가 완료 ({len(documents)}개 청크)")

    except Exception as e:
        print(f"⚠️ {filename} 처리 중 오류 발생: {e}")

print(f"\n🎉 총 {file_count}개 txt 문서를 벡터 DB에 저장 완료! (테스트용)")
print(f"📁 DB 경로: {db_path}")

# =============================================
# 📌 GitHub 자동 푸시 (날짜별 DB만)
# =============================================
subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"])
subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
subprocess.run(["git", "add", f"chroma_db/{today_str}"])
subprocess.run(["git", "commit", "-m", f"Auto update vector DB for {today_str}"])
subprocess.run(["git", "push"])
