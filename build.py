import os
import shutil
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# --- 設定 ---
TEMPLATES_DIR = 'templete'
OUTPUT_DIR = 'dist'  # 生成物をまとめるディレクトリ（慣習的にdistやpublicを使います）
STATIC_DIR = 'static'

# Jinja2の設定
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

# --- データ (本来はMarkdownから読み込む部分) ---
dummy_posts = [
    {
        "slug": "kichijoji-cafe-sample",
        "title": "吉祥寺で見つけた隠れ家！「Cafe Sample」の絶品プリン",
        "date": "2026-03-29",
        "area": "📍吉祥寺",
        "summary": "裏路地にある静かなカフェ。Wi-Fiもあって作業が捗りました。",
        "tags": ["プリン", "Wi-Fiあり", "おひとりさま"],
        "draft": False
    },
    {
        "slug": "daikanyama-bakery",
        "title": "【代官山】テラス席が気持ちいい！朝活におすすめのベーカリー",
        "date": "2026-03-28",
        "area": "📍代官山",
        "summary": "焼きたてのクロワッサンとコーヒーの香りに包まれる至福の朝食。",
        "tags": ["朝活", "テラス席", "パン"],
        "draft": False
    }
]

def validate_and_filter_posts(posts):
    """3.3 制約に基づいたバリデーションとフィルタリング"""
    valid_posts = []
    seen_slugs = set()

    for post in posts:
        # draft=true の記事は本番出力しない
        if post.get('draft'):
            continue

        # title は必須
        if not post.get('title'):
            print(f"Skip: Title is missing.")
            continue

        # slug は一意であること
        slug = post.get('slug')
        if not slug or slug in seen_slugs:
            print(f"Skip: Duplicate or missing slug '{slug}'.")
            continue
        seen_slugs.add(slug)

        # date は正しい日付形式であること
        try:
            datetime.strptime(post['date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            print(f"Skip: Invalid date format for {slug}.")
            continue

        # tags は配列であること
        if not isinstance(post.get('tags'), list):
            post['tags'] = []

        valid_posts.append(post)
    
    # 日付の新しい順にソート
    return sorted(valid_posts, key=lambda x: x['date'], reverse=True)

def build():
    # 1. 出力ディレクトリのクリーンアップと準備
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, 'articles'))
    os.makedirs(os.path.join(OUTPUT_DIR, 'tags'))

    # 静的ファイルのコピー (static/style.cssなど)
    if os.path.exists(STATIC_DIR):
        shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, STATIC_DIR))

    # 2. データの検証と加工
    posts = validate_and_filter_posts(dummy_posts)

    # タグ逆引きマップの作成
    tags_map = {}
    for post in posts:
        for tag in post['tags']:
            tags_map.setdefault(tag, []).append(post)

    # 3. 各ページの生成
    
    # A. トップページ (index.html)
    index_tmpl = env.get_template('index.html')
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_tmpl.render(posts=posts))

    # B. 記事詳細ページ (articles/{slug}.html)
    article_tmpl = env.get_template('article.html')
    for post in posts:
        output_path = os.path.join(OUTPUT_DIR, 'articles', f"{post['slug']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article_tmpl.render(post=post))

    # C. タグ一覧ページ (tags/index.html)
    tags_tmpl = env.get_template('tags.html')
    with open(os.path.join(OUTPUT_DIR, 'tags', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(tags_tmpl.render(tags_map=tags_map))

    # D. タグ別記事一覧 (tags/{tag}.html)
    tag_single_tmpl = env.get_template('tag_single.html')
    for tag_name, tagged_posts in tags_map.items():
        output_path = os.path.join(OUTPUT_DIR, 'tags', f"{tag_name}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tag_single_tmpl.render(tag_name=tag_name, posts=tagged_posts))

    print(f"Successfully built the blog in '{OUTPUT_DIR}/' directory!")

if __name__ == '__main__':
    build()