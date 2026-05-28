import bs4
import json

from .constants import SOUP_PARSER, URL_INDEX
from .models import Artist, Category, Character, Group, Hentai, Language, Parody, Tag
from .net import receive


def scrape_tag_container(container):
    meta = container.text.strip().replace("\n", "").replace("\t", "")

    tag_counts = container.find(class_="tags").find_all(class_="count")
    tags = [t.parent for t in tag_counts]
    assert len(tag_counts) == len(tags)
    tag_names = [t.find(class_="name").text for t in tags]
    tag_counts = [t.find(class_="count").text for t in tags]

    tag_links = []
    for t in tags:
        link = t["href"]
        if link.startswith("/"):
            link = link[1:]
        link = URL_INDEX + link
        tag_links.append(link)

    assert len(tags) == len(tag_names) == len(tag_counts) == len(tag_links)
    return meta, tag_names, tag_links, tag_counts


def scrape_index_hentai_cards(soup):
    hentais = []
    for card in soup.find_all("a", href=True):
        href = card["href"]
        if not href.startswith("/g/"):
            continue

        gallery_id = href[len("/g/") :].split("/")[0]
        if not gallery_id.isdigit():
            continue

        hentais.append(card)

    return hentais


def scrape_hentais(url_page):
    page_num = 0
    while True:
        page_num += 1

        url = url_page.format(page=page_num)
        data = receive(url)

        soup = bs4.BeautifulSoup(data, SOUP_PARSER)

        hentais_in_container = scrape_index_hentai_cards(soup)
        if len(hentais_in_container) == 0:
            while True:
                yield

        for hentai in hentais_in_container:
            link = hentai["href"]
            if link.endswith("/"):
                link = link[1:]
            link = URL_INDEX + link

            title_tag = hentai.find(class_="caption")
            if title_tag is not None:
                title = title_tag.text
            else:
                title = hentai.get("title")
                if title is None or title.strip() == "":
                    title = hentai.get_text(" ", strip=True)
                if title.strip() == "":
                    title = link

            id_ = link.split("/")[-2]
            id_ = int(id_)

            # Fetch gallery data from official API for reliable extraction
            soup = None
            try:
                api_url = f"https://nhentai.net/api/v2/galleries/{id_}"
                api_response = receive(api_url)
                api_data = json.loads(api_response)

                # Extract thumbnail URL from API
                thumb_obj = api_data.get("thumbnail", {})
                thumb_path = thumb_obj.get("path")
                if thumb_path:
                    thumb = f"https://t.nhentai.net/{thumb_path}"
                else:
                    thumb = None

                # Extract page count from API
                pages = api_data.get("num_pages")

            except Exception:
                # Fallback to HTML scraping if API fails
                data = receive(link)
                soup = bs4.BeautifulSoup(data, SOUP_PARSER)

                thumb_tag = soup.find(class_="lazyload")
                if thumb_tag is None:
                    thumb_tag = soup.find("img")
                if thumb_tag is not None:
                    src = thumb_tag.get("src")
                    if src and ("nhentai.net" in src or "t" in src):
                        thumb = src
                    else:
                        thumb = None
                else:
                    thumb = None

                # Parse page count from HTML as fallback
                containers = soup.find_all(class_="tag-container field-name") + soup.find_all(
                    class_="tag-container field-name hidden"
                )
                pages = None
                for container in containers:
                    meta = container.text.strip().replace("\n", "").replace("\t", "")
                    if meta.startswith("Pages:"):
                        pages_str = meta[len("Pages:"):].strip()
                        try:
                            pages = int(pages_str)
                        except ValueError:
                            pages = None
                        break

            # If API succeeded but we don't have soup yet, get it for tag extraction
            if soup is None:
                data = receive(link)
                soup = bs4.BeautifulSoup(data, SOUP_PARSER)

            containers = soup.find_all(class_="tag-container field-name") + soup.find_all(
                class_="tag-container field-name hidden"
            )
            tags = []
            languages = []
            categories = []
            parodies = []
            characters = []
            artists = []
            groups = []
            uploaded = None
            for container in containers:
                meta, n, l, c = scrape_tag_container(container)

                if meta.startswith("Uploaded:"):
                    uploaded = meta[len("Uploaded:") :] + " (this time is currently bugged)"
                else:
                    for n, l, c in zip(n, l, c):
                        if meta.startswith("Tags:"):
                            tags.append(Tag(n, l, c))
                        elif meta.startswith("Languages:"):
                            languages.append(Language(n, l, c))
                        elif meta.startswith("Categories:"):
                            categories.append(Category(n, l, c))
                        elif meta.startswith("Parodies:"):
                            parodies.append(Parody(n, l, c))
                        elif meta.startswith("Characters:"):
                            characters.append(Character(n, l, c))
                        elif meta.startswith("Artists:"):
                            artists.append(Artist(n, l, c))
                        elif meta.startswith("Groups:"):
                            groups.append(Group(n, l, c))
                        else:
                            assert False

            yield Hentai(
                id_,
                title,
                link,
                thumb,
                tags,
                languages,
                categories,
                pages,
                uploaded,
                parodies,
                characters,
                artists,
                groups,
            )

