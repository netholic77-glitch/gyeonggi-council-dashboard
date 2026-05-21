#!/usr/bin/env python3
"""경기도의회 후보자 뉴스 대시보드 자동 생성 스크립트 (GitHub Actions용)"""

import json, os, time, urllib.parse, re
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
today = datetime.now(KST)
update_time = today.strftime('%Y년 %m월 %d일 %H:%M KST')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

with open(os.path.join(SCRIPT_DIR, 'candidates.json'), encoding='utf-8') as f:
    candidates = json.load(f)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Referer': 'https://www.naver.com/'
}

def search_naver_news(name, sgg):
    query = f"{name} 경기도의원"
    url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(query)}&sort=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = soup.select('li.bx') or soup.select('.news_wrap')
        for item in items[:1]:
            title_el = item.select_one('a.news_tit')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get('href', '')
            date_el = item.select_one('.info_group .info:last-child') or item.select_one('.date')
            date_str = date_el.get_text(strip=True) if date_el else ''
            if title and link:
                return {'has_news': True, 'title': title, 'link': link, 'date': date_str}
        return {'has_news': False, 'title': '', 'link': '', 'date': ''}
    except Exception as e:
        print(f"  오류: {name} - {e}")
        return {'has_news': False, 'title': '', 'link': '', 'date': ''}

print(f"뉴스 검색 시작: {len(candidates)}명")
results = []
for i, c in enumerate(candidates):
    print(f"[{i+1}/{len(candidates)}] {c['name']} ({c['sgg']})", end=' ')
    news = search_naver_news(c['name'], c['sgg'])
    results.append({**c, **news})
    print('✓' if news['has_news'] else '-')
    time.sleep(0.4)

news_count = sum(1 for r in results if r['has_news'])
print(f"\n완료: 뉴스 있음 {news_count}명 / 전체 {len(results)}명")

PARTY_COLORS = {
    '더불어민주당': '#0052A5',
    '국민의힘': '#E61E2B',
    '개혁신당': '#FF7210',
    '진보당': '#D6001C',
    '조국혁신당': '#003C8F',
    '무소속': '#888888'
}

def party_badge(party):
    color = PARTY_COLORS.get(party, '#888888')
    return f'<span class="badge" style="background:{color}">{party}</span>'

rows = ''
for r in results:
    news_html = ''
    if r['has_news']:
        news_html = f'<a href="{r["link"]}" target="_blank" class="news-link">{r["title"]}</a><span class="news-date">{r["date"]}</span>'
    else:
        news_html = '<span class="no-news">뉴스 없음</span>'
    rows += f'''<tr data-city="{r['city']}" data-party="{r['party']}" data-has-news="{'true' if r['has_news'] else 'false'}">
      <td>{r['no']}</td>
      <td>{r['sgg']}</td>
      <td class="name-cell">{r['name_full']}</td>
      <td>{party_badge(r['party'])}</td>
      <td class="news-cell">{news_html}</td>
    </tr>'''

cities = sorted(set(r['city'] for r in results))
city_opts = '<option value="">전체 시·군</option>' + ''.join(f'<option value="{c}">{c}</option>' for c in cities)

parties = sorted(set(r['party'] for r in results))
party_opts = '<option value="">전체 정당</option>' + ''.join(f'<option value="{p}">{p}</option>' for p in parties)

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>경기도의회 후보자 뉴스 대시보드</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans KR", sans-serif; background: #f5f7fa; color: #1a1a2e; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: white; padding: 24px 32px; }}
.header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
.header .meta {{ font-size: 12px; opacity: 0.7; margin-top: 6px; }}
.controls {{ background: white; border-bottom: 1px solid #e8eaed; padding: 16px 32px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
.controls input {{ padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; min-width: 200px; }}
.controls select {{ padding: 8px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 13px; background: white; cursor: pointer; }}
.controls .stats {{ margin-left: auto; font-size: 12px; color: #6b7280; }}
table {{ width: 100%; border-collapse: collapse; background: white; }}
th {{ padding: 12px 14px; text-align: left; font-weight: 600; font-size: 12px; letter-spacing: 0.3px; white-space: nowrap; background: #f8fafc; border-bottom: 2px solid #e2e8f0; color: #475569; text-transform: uppercase; }}
td {{ padding: 11px 14px; border-bottom: 1px solid #f1f5f9; font-size: 13px; vertical-align: middle; }}
tr:hover td {{ background: #f8faff; }}
.badge {{ display: inline-block; padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; color: white; white-space: nowrap; }}
.name-cell {{ font-weight: 600; }}
.news-cell {{ max-width: 420px; }}
.news-link {{ color: #1d4ed8; text-decoration: none; font-size: 12.5px; display: block; line-height: 1.5; }}
.news-link:hover {{ text-decoration: underline; }}
.news-date {{ font-size: 11px; color: #94a3b8; margin-top: 2px; display: block; }}
.no-news {{ color: #cbd5e1; font-size: 12px; }}
.table-wrap {{ overflow-x: auto; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 20px 24px; }}
tr.hidden {{ display: none; }}
</style>
</head>
<body>
<div class="header">
  <h1>🏛 경기도의회 후보자 뉴스 대시보드</h1>
  <div class="meta">자동 업데이트: {update_time} &nbsp;|&nbsp; 총 {len(results)}명 &nbsp;|&nbsp; 뉴스 있음 {news_count}명</div>
</div>
<div class="controls">
  <input type="text" id="search" placeholder="후보자 이름 또는 선거구 검색...">
  <select id="cityFilter">{city_opts}</select>
  <select id="partyFilter">{party_opts}</select>
  <select id="newsFilter">
    <option value="">전체</option>
    <option value="true">뉴스 있음</option>
    <option value="false">뉴스 없음</option>
  </select>
  <span class="stats" id="stats"></span>
</div>
<div class="table-wrap">
<table id="mainTable">
<thead><tr>
  <th>번호</th><th>선거구</th><th>후보자</th><th>정당</th><th>관련 뉴스</th>
</tr></thead>
<tbody id="tbody">
{rows}
</tbody>
</table>
</div>
<script>
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  const city = document.getElementById('cityFilter').value;
  const party = document.getElementById('partyFilter').value;
  const news = document.getElementById('newsFilter').value;
  const rows = document.querySelectorAll('#tbody tr');
  let shown = 0;
  rows.forEach(r => {{
    const text = r.textContent.toLowerCase();
    const match = (!q || text.includes(q)) &&
      (!city || r.dataset.city === city) &&
      (!party || r.dataset.party === party) &&
      (!news || r.dataset.hasNews === news);
    r.classList.toggle('hidden', !match);
    if (match) shown++;
  }});
  document.getElementById('stats').textContent = shown + '명 표시 중';
}}
['search','cityFilter','partyFilter','newsFilter'].forEach(id => {{
  document.getElementById(id).addEventListener('input', filterTable);
}});
filterTable();
</script>
</body>
</html>'''

out_path = os.path.join(REPO_ROOT, 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"index.html 저장 완료: {out_path}")
