import urllib.request

urls = [
    "http://127.0.0.1:8088/",
    "http://127.0.0.1:8088/notes/",
    "http://127.0.0.1:8088/projects/",
    "http://127.0.0.1:8088/resume/",
]
need = {
    "http://127.0.0.1:8088/": ["Главная", "Проекты", "Резюме", "Заметки", "Контакты", "Обо мне", "CopyParse", "--wp--preset--color--base: #f6f3ec", "GitHub"],
    "http://127.0.0.1:8088/notes/": ["Заметки", "Как устроено рабочее место"],
}
bad = ["FAQs", "Fleurs", "Stories", ">Blog<", "Shop", "Patterns", "Themes"]
for url in urls:
    with urllib.request.urlopen(url, timeout=20) as response:
        html = response.read().decode("utf-8", "replace")
        print(response.status, url, "len", len(html))
    for needle in need.get(url, []):
        print(" ", "OK" if needle in html else "MISSING", needle)
    found = [item for item in bad if item in html]
    print("  unwanted", found or "-")
