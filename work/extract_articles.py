from bs4 import BeautifulSoup

def extract_ids_and_titles(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # BeautifulSoupを使用してXMLをパース
    soup = BeautifulSoup(content, 'lxml-xml')
    articles = []

    # Find all items in the XML (each item represents a post)
    for item in soup.find_all('item'):
        title_tag = item.find('title')
        guid_tag = item.find('guid', isPermaLink="false")
        
        if title_tag and guid_tag:
            title = title_tag.text.strip()
            guid_text = guid_tag.text.strip()
            
            # ?p=の後のIDを抽出
            if '?p=' in guid_text:
                post_id = guid_text.split('?p=')[1]
                articles.append({'ID': post_id, 'Title': title})

    return articles

# ファイルパスを指定
file_path = '/Users/miyashitahiroshinozomi/ALBINO/asp/wp/raysee.WordPress.2024-06-20.xml'

# 抽出関数を使用してIDとタイトルを取得
articles = extract_ids_and_titles(file_path)

# 抽出されたIDとタイトルをコンソールに表示
for article in articles:
    print(f"{article['Title']}")
