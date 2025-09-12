from flask import Flask, request, send_from_directory, jsonify
from datetime import datetime
from bs4 import BeautifulSoup
import os
import requests
import bleach

# Статические файлы теперь из корня
app = Flask(__name__, static_url_path='', static_folder='.')

# Настройки безопасности
ALLOWED_EXTENSIONS = {'.html'}
SITE_DIR = os.path.abspath(os.path.dirname(__file__))  # Корень сайта
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe')





def is_safe_path(path):
    """Проверяет, что путь находится внутри разрешенной директории."""
    abs_path = os.path.abspath(path)
    return abs_path.startswith(SITE_DIR)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# Убрали /site/ — теперь отдаём напрямую из корня
@app.route('/<path:filename>', methods=["GET"])
def serve_root(filename):
    return send_from_directory('.', filename)


@app.route("/vote", methods=["POST"])
def vote_comment():
    data = request.get_json()
    page_path = data.get("page", "").lstrip("/")
    comment_id = data.get("comment_id")
    previous_vote = data.get("previous_vote")
    new_vote = data.get("new_vote")

    if not page_path or not comment_id:
        return jsonify(success=False, message="Missing page or comment ID"), 400

    file_path = os.path.join(SITE_DIR, page_path)

    if not is_safe_path(file_path) or not os.path.exists(file_path):
        return jsonify(success=False, message="Page not found"), 404

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'html.parser')

        rating_div = soup.find('div', attrs={'data-comment-id': str(comment_id)})
        if not rating_div:
            return jsonify(success=False, message="Comment rating block not found"), 404

        rating_span = rating_div.find('span', class_='ratingtypeplusminus')
        if not rating_span:
            return jsonify(success=False, message="Rating span not found"), 404

        current_rating = int(rating_span.string.strip().replace('+', ''))

        rating_change = 0
        if previous_vote == 'like': rating_change -= 1
        elif previous_vote == 'dislike': rating_change += 1

        if new_vote == 'like': rating_change += 1
        elif new_vote == 'dislike': rating_change -= 1

        new_rating = current_rating + rating_change

        rating_span.string = f"{'+' if new_rating > 0 else ''}{new_rating if new_rating != 0 else '0'}"

        comment_div = rating_div.find_parent('div', class_='js-comm')
        if comment_div:
            new_classes = [c for c in comment_div.get('class', []) if c not in ['pos', 'neg']]
            if new_rating > 0:
                new_classes.append('pos')
            elif new_rating < 0:
                new_classes.append('neg')
            comment_div['class'] = new_classes

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        return jsonify(success=True, new_rating=new_rating)
    except Exception as e:
        print("Ошибка при обработке голоса:", e)
        return jsonify(success=False, message=str(e)), 500


@app.route("/rate-page", methods=["POST"])
def rate_page():
    data = request.get_json()
    page_path = data.get("page_path", "").lstrip("/")
    previous_vote = data.get("previous_vote")
    new_vote = data.get("new_vote")

    if not page_path:
        return jsonify(success=False, message="Missing page path"), 400

    file_path = os.path.join(SITE_DIR, page_path)
    if not is_safe_path(file_path) or not os.path.exists(file_path):
        return jsonify(success=False, message="Page not found"), 404

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, 'html.parser')

        # Теперь ищем по классам, а не по data-id
        like_spans = soup.find_all('span', class_='page-likes-count')
        dislike_spans = soup.find_all('span', class_='page-dislikes-count')
        score_div = soup.find('div', class_='content-page__ratingscore-ring')

        if not like_spans or not dislike_spans:
            return jsonify(success=False, message="Rating spans not found"), 404

        current_likes = int(like_spans[0].string)
        current_dislikes = int(dislike_spans[0].string)

        like_change = 0
        dislike_change = 0

        if previous_vote == 'like':
            like_change = -1
        elif previous_vote == 'dislike':
            dislike_change = -1

        if new_vote == 'like':
            like_change += 1
        elif new_vote == 'dislike':
            dislike_change += 1

        new_likes = current_likes + like_change
        new_dislikes = current_dislikes + dislike_change

        total_votes = new_likes + new_dislikes
        new_score = 0
        if total_votes > 0:
            new_score = round((new_likes / total_votes) * 10)

        new_score_percent = new_score * 10

        for span in like_spans:
            span.string = str(new_likes)
        for span in dislike_spans:
            span.string = str(new_dislikes)

        if score_div:
            score_div.string = str(new_score)
            score_div['style'] = f"--p:{new_score_percent}%;"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))

        return jsonify(success=True, new_likes=new_likes, new_dislikes=new_dislikes, new_score=new_score, new_score_percent=new_score_percent)

    except Exception as e:
        print(f"Ошибка при обработке голоса за страницу: {e}")
        return jsonify(success=False, message=str(e)), 500


@app.route('/add-comment', methods=['POST'])
def add_comment():
    data = request.json
    name_raw = data.get("name", "Гость")
    comment_text_raw = data.get("comment", "")
    page_path_raw = data.get("page", "").lstrip("/")
    parent_id_raw = data.get("parent_id")
    recaptcha_token = data.get("g-recaptcha-response")

    if not recaptcha_token:
        return "reCAPTCHA token is missing", 400

    # Всегда выполнять проверку reCAPTCHA
    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_token
    })
    google_response = r.json()
    if not google_response.get('success'):
        return "reCAPTCHA verification failed", 400

    name = bleach.clean(name_raw, tags=[], strip=True)
    comment_text = bleach.clean(comment_text_raw, tags=['b', 'i', 'u', 's', 'a'], attributes={'a': ['href']}, strip=True)
    parent_id = bleach.clean(str(parent_id_raw), tags=[], strip=True) if parent_id_raw else None

    if not comment_text or not page_path_raw.endswith(".html"):
        return "Invalid input", 400

    file_path = os.path.join(SITE_DIR, page_path_raw)
    if not is_safe_path(file_path) or not os.path.exists(file_path):
        return "Page not found", 404

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    first_letter = name.strip()[0].upper() if name.strip() else 'Г'
    comment_id = str(int(datetime.now().timestamp()))
    new_comment_html = f'''
<li class="comments-tree-item" style="list-style: none;">
<div id="comment-{comment_id}" class="comm js-comm">
  <div class="comment__header d-flex ai-center c-gap-10">
    <div class="comment__img img-block ratio-1-1 js-comm-avatar">
      <img src="/assets/lordfilm-website/siteimages/noavatar.png" alt="{name}" loading="lazy">
      <div class="comment__letter d-flex jc-center ai-center" style="background-color:#95a5a6">{first_letter}</div>
    </div>
    <div class="comment__meta flex-1 d-flex ai-center c-gap-20">
      <div class="comment__author js-comm-author d-flex ai-center c-gap-10">
        <span>{name}</span>
      </div>
      <div class="comment__date ws-nowrap">{now}</div>
    </div>
    <div class="comment__rating d-flex ai-center c-gap-10" data-comment-id="{comment_id}">
      <a href="#" class="vote-btn" data-vote="like"><span class="fal fa-thumbs-up"></span></a>
      <span class="ratingtypeplusminus">0</span>
      <a href="#" class="vote-btn" data-vote="dislike"><span class="fal fa-thumbs-down"></span></a>
    </div>
  </div>
  <div class="comment__text rich-text clearfix">
    <div>{comment_text}</div>
  </div>
  <div class="comment__footer d-flex ai-center r-gap-10 c-gap-10">
    <ul class="comment__action d-flex ai-center c-gap-20">
      <li class="comment__action-reply d-flex ai-center c-gap-5 fal fa-chevron-down"><a href="#">Ответить</a></li>
    </ul>
  </div>
</div>
</li>
'''

    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    comment_soup = BeautifulSoup(new_comment_html, 'html.parser')
    li_element = comment_soup.find('li')

    if parent_id:
        parent_rating_div = soup.find('div', attrs={'data-comment-id': str(parent_id)})
        if not parent_rating_div:
            return "Parent comment not found", 404
        
        parent_li = parent_rating_div.find_parent('li', class_='comments-tree-item')
        if not parent_li:
            return "Parent li item not found", 404

        children_container = parent_li.find('ul', class_='comments-tree-children')
        if not children_container:
            children_container = soup.new_tag('ul', **{'class': 'comments-tree-children'})
            parent_li.append(children_container)
        
        children_container.append(li_element)
    else:
        comments_container = soup.find(id='content-page__comments-list')
        if not comments_container:
            return "Comment block not found", 500
        no_comments_message = comments_container.find_previous_sibling('div', class_='message-info')
        if no_comments_message:
            no_comments_message.decompose()
            current_classes = comments_container.get('class', [])
            if 'content-page__comments-list--not-comments' in current_classes:
                current_classes.remove('content-page__comments-list--not-comments')
                comments_container['class'] = current_classes

        comments_container.append(li_element)

    all_comments = soup.find_all('li', class_='comments-tree-item')
    comments_count = len(all_comments)
    
    title_div = soup.find('div', class_='section__title')
    if title_div:
        title_div.string = f"Комментарии ({comments_count})"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    return str(li_element), 200


if __name__ == '__main__':
    app.run(debug=True)
