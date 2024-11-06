from flask import Flask, request, jsonify
from flask_cors import CORS  # CORS 임포트
from bs4 import BeautifulSoup
import requests
import time

app = Flask(__name__)
CORS(app)  # 모든 도메인에서 요청을 허용하도록 CORS 적용

# 기본 경로('/') 처리 추가
@app.route('/')
def home():
    return jsonify(message="Welcome to the SEO Analyzer API!")

def calculate_seo_score(data):
    score = 0
    recommendations = []

    if data["title"] != "없음":
        score += 10
    else:
        recommendations.append("Title 태그를 추가하세요.")

    if data["description"] != "없음":
        score += 10
    else:
        recommendations.append("Description 메타 태그를 추가하세요.")

    if data["keywords"] != "없음":
        score += 5
    else:
        recommendations.append("Keywords 메타 태그를 추가하는 것이 좋습니다.")

    alt_tags_ratio = int(data["alt_tag_count"].split('/')[0]) / int(data["alt_tag_count"].split('/')[1]) if int(data["alt_tag_count"].split('/')[1]) > 0 else 0
    if alt_tags_ratio >= 0.8:
        score += 10
    else:
        recommendations.append("모든 이미지에 Alt 태그를 추가하여 접근성을 높이세요.")

    if data["canonical_status"] == "존재함":
        score += 5
    else:
        recommendations.append("Canonical 태그를 설정하여 중복 콘텐츠 문제를 해결하세요.")

    if data["ssl_status"] == "HTTPS 사용":
        score += 10
    else:
        recommendations.append("웹사이트에 SSL 인증서를 적용하여 보안을 강화하세요.")

    if data["mobile_friendly"] == "모바일 친화적":
        score += 10
    else:
        recommendations.append("웹사이트를 모바일 친화적으로 개선하세요.")

    response_time = float(data["response_time"].replace("초", ""))
    if response_time <= 2.0:
        score += 10
    else:
        recommendations.append("페이지 로딩 시간을 2초 이하로 줄이세요.")

    if data["social_media_meta"] == "존재함":
        score += 5
    else:
        recommendations.append("소셜 미디어 메타 태그를 추가하여 콘텐츠 공유를 최적화하세요.")

    if data["language"] != "없음":
        score += 5
    else:
        recommendations.append("언어 설정을 추가하여 검색 엔진이 사이트 언어를 인식할 수 있도록 하세요.")

    if data["custom_404"] == "설정됨":
        score += 5
    else:
        recommendations.append("사용자 지정 404 페이지를 설정하여 방문자가 잘못된 URL로 접근할 때 유용한 정보를 제공하세요.")

    if data["duplicate_content"] == "없음":
        score += 5
    else:
        recommendations.append("중복 콘텐츠를 제거하거나 Canonical 태그를 활용하세요.")

    return min(score, 100), recommendations

def get_score_text(score):
    if score >= 90:
        return "최적화가 매우 잘 되어 있습니다."
    elif score >= 80:
        return "양호한 최적화 상태입니다."
    elif score >= 60:
        return "개선할 부분이 있지만 괜찮은 상태입니다."
    elif score >= 40:
        return "개선이 필요합니다."
    else:
        return "심각한 최적화 문제가 있습니다. 즉각적인 개선이 필요합니다."

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.json.get('url')
    
    if not url.startswith('http'):
        url = 'https://' + url

    try:
        start_time = time.time()
        response = requests.get(url)
        response_time = time.time() - start_time
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else "없음"
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else "없음"
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = keywords['content'] if keywords else "없음"
        
        images = soup.find_all('img')
        alt_tags = [img for img in images if img.get('alt')]
        alt_tag_count = len(alt_tags)
        
        canonical = soup.find('link', rel='canonical')
        canonical_status = "존재함" if canonical else "없음"

        ssl_status = "HTTPS 사용" if url.startswith('https') else "HTTPS 미사용"

        content_length = len(response.text)
        cta_count = len([a for a in soup.find_all('a') if 'cta' in (a.get('class') or [])])
        internal_links = len([a for a in soup.find_all('a', href=True) if url in a['href']])
        external_links = len([a for a in soup.find_all('a', href=True) if url not in a['href']])
        mobile_friendly = "모바일 친화적"
        language = soup.html.get('lang', '없음')
        duplicate_content = "없음"
        
        test_404_url = url.rstrip('/') + '/nonexistentpage'
        custom_404_response = requests.get(test_404_url)
        custom_404 = "설정됨" if custom_404_response.status_code == 404 and len(custom_404_response.text) > 0 else "설정되지 않음"
        
        social_media_meta = "존재함" if soup.find('meta', property="og:title") else "없음"

        data = {
            "title": title,
            "description": description,
            "keywords": keywords,
            "alt_tag_count": f"{alt_tag_count}/{len(images)}",
            "canonical_status": canonical_status,
            "ssl_status": ssl_status,
            "response_time": f"{response_time:.2f}초",
            "content_length": f"{content_length}자",
            "internal_links": internal_links,
            "external_links": external_links,
            "cta_count": cta_count,
            "mobile_friendly": mobile_friendly,
            "language": language,
            "duplicate_content": duplicate_content,
            "social_media_meta": social_media_meta,
            "custom_404": custom_404
        }

        score, recommendations = calculate_seo_score(data)
        data["score"] = score
        data["score_text"] = get_score_text(score)
        data["recommendations"] = recommendations

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
