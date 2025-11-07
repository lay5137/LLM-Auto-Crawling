import os
import re
import time
import openpyxl
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import subprocess


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# ✅ 크롬드라이버 설치 및 설정
chromedriver_autoinstaller.install()
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(), options=chrome_options)
driver.implicitly_wait(5)

# ✅ 저장 경로 (GitHub 저장소 내부 폴더)
save_base = './result_files'
os.makedirs(save_base, exist_ok=True)

excel_path = os.path.join(save_base, "crawl_result.xlsx")

# ✅ 엑셀 파일 초기화 or 불러오기 (🔹 URL 열 추가)
if not os.path.exists(excel_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "게시글 목록"
    ws.append(["게시글 제목", "작성자", "작성일", "URL"])  # ✅ URL 열 추가
    wb.save(excel_path)
    existing_keys = set()
else:
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    existing_keys = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        title, writer, date, *_ = row  # ✅ URL은 무시하고 기존 키 유지
        if title and date:
            existing_keys.add(f"{title.strip()}_{date.strip()}")
    print(f"✅ 기존 게시글 {len(existing_keys)}건 로드 완료.")


# ✅ URL 포함하도록 수정
def append_to_excel(title, writer, date, url, excel_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    ws.append([title, writer, date, url])  # ✅ URL 저장 추가
    wb.save(excel_path)


# ===============================
# 공주대 SW중심대학 공지사항 크롤러
# ===============================
base_url = "https://swknu.kongju.ac.kr"
board_url = f"{base_url}/community/notice.do?&pn=6"
max_pages = 1  # 최대 페이지 수

print(f"\n========== 🔍 공주대 SW중심대학 공지사항 크롤링 시작 ==========")

driver.get(board_url)
page_num = 4

while True:
    print(f"\n📄 {page_num}페이지 처리 중... ({driver.current_url})")
    items = driver.find_elements(By.CSS_SELECTOR, ".list-photo .item")

    if not items:
        print("❌ 게시글 항목을 찾을 수 없음, 종료.")
        break

    for idx, item in enumerate(items, start=1):
        try:
            link_elem = item.find_element(By.CSS_SELECTOR, "a[href*='noticedetail.do']")
            title = item.find_element(By.CSS_SELECTOR, ".title").text.strip()
            post_url = urljoin(base_url, link_elem.get_attribute("href"))
            info_elems = item.find_elements(By.CSS_SELECTOR, ".post-info span")

            writer = info_elems[0].text.strip() if len(info_elems) > 0 else "정보 없음"
            date = info_elems[1].text.strip() if len(info_elems) > 1 else "정보 없음"

            key = f"{title}_{date}"
            if key in existing_keys:
                print(f"⏩ ({idx}) {title} ({date}) → 이미 존재, 건너뜀")
                continue

            print(f"📰 ({idx}) {title} ({date}) → 새 게시글 처리 중...")

            driver.get(post_url)
            time.sleep(1)

            try:
                content_elem = driver.find_element(By.CSS_SELECTOR, ".view-note")
                content = content_elem.text.strip()
            except:
                content = "본문을 가져올 수 없습니다."

            file_links = []
            try:
                file_elems = driver.find_elements(By.CSS_SELECTOR, "div.post-file ul li a")
                for f in file_elems:
                    fname = f.text.strip()
                    furl = urljoin(base_url, f.get_attribute("href"))
                    if fname and fname != "미리보기":
                        file_links.append((fname, furl))
            except:
                pass

            safe_title = sanitize_filename(title)[:80]
            file_path = os.path.join(save_base, f"{safe_title}.md")

            markdown = f"""# {title}

**작성자:** {writer}  
**작성일:** {date}  

---

## 본문
{content}

---

## 첨부파일
"""
            if file_links:
                for fname, furl in file_links:
                    markdown += f"- [{fname}]({furl})\n"
            else:
                markdown += "첨부파일 없음\n"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown)

            # ✅ URL 인자 추가
            append_to_excel(title, writer, date, post_url, excel_path)
            existing_keys.add(key)
            print(f"✅ 저장 완료 → {file_path}")

            driver.back()
            time.sleep(1)

        except Exception as e:
            print(f"❗ 게시글 처리 실패: {e}")
            continue

    try:
        next_page = driver.find_element(By.CSS_SELECTOR, f"a[href*='pn={page_num+1}']")
        driver.get(next_page.get_attribute("href"))
        page_num += 1
        if page_num > max_pages:
            print(f"🔒 최대 {max_pages}페이지 도달 → 종료")
            break
    except:
        print("📄 다음 페이지 없음 → 종료")
        break

driver.quit()
print("\n✅ 모든 크롤링 완료!")

# ✅ GitHub에 자동 푸시
subprocess.run(["git", "config", "--global", "user.email", "github-actions@github.com"])
subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Auto update crawl results"])
subprocess.run(["git", "push"])
