# ============================================
# 📘 MD → TXT 변환 (LLM 재작성 전용)
# ============================================

import os
import time
from openai import OpenAI

# ============================================
# 📌 경로 설정 (Actions 환경)
# ============================================
md_folder = "./result_files"   # crawler.py가 저장한 MD 파일 폴더
txt_folder = "./result_txt"    # 변환 후 TXT 파일 저장 폴더
os.makedirs(txt_folder, exist_ok=True)

# ============================================
# 📌 LLM 클라이언트 초기화
# ============================================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ============================================
# 📌 LLM 재작성 함수
# ============================================
def rewrite_md_with_llm(md_content):
    prompt = f"""
다음 Markdown 텍스트를 자연스러운 문장 구조의 한글 텍스트로 변환해주세요.
의미와 정보는 유지하되, 마크다운 문법(#, -, *, ``` 등)은 제거하고 매끄러운 문단으로 재구성합니다.
표, 리스트, 헤더 등은 문장형으로 풀어주세요.
새로운 내용은 절대 추가하지 마세요.

텍스트:
{md_content}
"""
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=8000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print("⚠️ LLM 실패, 재시도 중:", e)
            time.sleep(2)
    return md_content  # 실패 시 원본 반환

# ============================================
# 📌 전체 MD 파일 변환
# ============================================
file_count = 0
for filename in os.listdir(md_folder):
    if filename.endswith(".md"):
        base_name = os.path.splitext(filename)[0]
        md_path = os.path.join(md_folder, filename)
        txt_path = os.path.join(txt_folder, f"{base_name}.txt")

        if os.path.exists(txt_path):
            print(f"⚠️ {base_name}.txt 이미 존재 → 변환 생략")
            continue

        print(f"📄 {filename} 변환 중...")

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        rewritten_text = rewrite_md_with_llm(md_content)

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(rewritten_text)

        file_count += 1
        print(f"✅ {filename} → {base_name}.txt 저장 완료")

print(f"\n🎉 총 {file_count}개 md 문서를 txt로 변환 완료!")
print(f"📁 저장 경로: {txt_folder}")