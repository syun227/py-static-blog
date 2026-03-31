import os
import shutil
import glob
import markdown
import frontmatter
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# --- 設定 ---
TEMPLATES_DIR = 'templete'
OUTPUT_DIR = 'dist'
STATIC_DIR = 'static'
CONTENT_DIR = 'content'

# Jinja2の設定
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def load_posts():
    """contentディレクトリ内の.mdファイルを読み込み、リストとして返す"""
    posts = []
    # .mdファイルを探す
    md_files = glob.glob(os.path.join(CONTENT_DIR, '*.md'))
    
    for file_path in md_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Front Matterと本文を分離して解析
            post_data = frontmatter.load(f)
            
            # Markdown本文をHTMLに変換
            html_content = markdown.markdown(post_data.content, extensions=['fenced_code', 'tables'])
            
            # 記事データを作成
            post = {
                "slug": os.path.splitext(os.path.basename(file_path))[0],
                "content": html_content,
                **post_data.metadata  # title, date, tagsなどが展開される
            }
            posts.append(post)
    return posts

def validate_and_filter_posts(posts):
    valid_posts = []
    seen_slugs = set()
    for post in posts:
        if post.get('draft'): continue
        if not post.get('title'): continue
        
        slug = post.get('slug')
        if not slug or slug in seen_slugs: continue
        seen_slugs.add(slug)

        try:
            # 日付オブジェクトに変換しておくとテンプレートで扱いやすくなります
            post['date_obj'] = datetime.strptime(post['date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            continue

        if not isinstance(post.get('tags'), list): post['tags'] = []
        valid_posts.append(post)
    
    return sorted(valid_posts, key=lambda x: x['date'], reverse=True)

def validate_and_filter_posts(posts):
    """制約に基づいたバリデーションとフィルタリング"""
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
            post['date_obj'] = datetime.strptime(post['date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            continue

        # tags は配列であること
        if not isinstance(post.get('tags'), list):
            post['tags'] = []

        valid_posts.append(post)
    
    # 日付の新しい順にソート
    return sorted(valid_posts, key=lambda x: x['date'], reverse=True)

def build():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    os.makedirs(os.path.join(OUTPUT_DIR, 'articles'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'tags'), exist_ok=True)

    if os.path.exists(STATIC_DIR):
        shutil.copytree(STATIC_DIR, os.path.join(OUTPUT_DIR, STATIC_DIR))

    raw_posts = load_posts() 
    posts = validate_and_filter_posts(raw_posts)

    tags_map = {}
    for post in posts:
        for tag in post['tags']:
            tags_map.setdefault(tag, []).append(post)

    article_tmpl = env.get_template('article.html')
    for post in posts:
        output_path = os.path.join(OUTPUT_DIR, 'articles', f"{post['slug']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(article_tmpl.render(post=post))

    print(f"Build Completed! Total {len(posts)} posts processed.")

if __name__ == '__main__':
    build()