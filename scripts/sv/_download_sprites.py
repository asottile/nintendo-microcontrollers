from __future__ import annotations

import concurrent.futures
import html.parser
import os.path
import time
import urllib.request

URL = 'https://pokemondb.net/pokedex/game/scarlet-violet'


class FindImages(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images = [
            'https://img.pokemondb.net/sprites/scarlet-violet/normal/oinkologne-male.png',  # noqa: E501
            'https://img.pokemondb.net/sprites/scarlet-violet/normal/oinkologne-female.png',  # noqa: E501
            'https://img.pokemondb.net/sprites/scarlet-violet/normal/maushold-family3.png',  # noqa: E501
            'https://img.pokemondb.net/sprites/scarlet-violet/normal/maushold-family4.png',  # noqa: E501
            'https://www.pokewiki.de/images/4/44/Pok%C3%A9mon-Icon_1011_KAPU.png',  # noqa: E501
            'https://www.pokewiki.de/images/5/58/Pok%C3%A9mon-Icon_1012_KAPU.png',  # noqa: E501
            'https://www.pokewiki.de/images/f/fd/Pok%C3%A9mon-Icon_1013_KAPU.png',  # noqa: E501
        ]

    def handle_starttag(
            self,
            tag: str,
            attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != 'img':
            return

        attrs_d = dict(attrs)
        if attrs_d.get('class') != 'img-fixed img-sprite img-sprite-v21':
            return

        src = attrs_d['src']
        assert src is not None

        if 'maushold' in src or 'oinkologne' in src:
            return

        # https://img.pokemondb.net/sprites/scarlet-violet/normal/2x/sprigatito.jpg
        self.images.append(src.replace('/2x/', '/').replace('.jpg', '.png'))


def req(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'asottile/nintendo-microcontrollers'},
    )
    time.sleep(.05)
    for _ in range(3):
        try:
            return urllib.request.urlopen(req, timeout=1).read()
        except Exception:
            print('R', end='', flush=True)
    else:
        raise AssertionError(f'too many retries for {url}')


def _download_one(url: str) -> None:
    target = os.path.basename(url)
    target = {
        'Pok%C3%A9mon-Icon_1011_KAPU.png': 'dipplin.png',
        'Pok%C3%A9mon-Icon_1012_KAPU.png': 'poltchageist.png',
        'Pok%C3%A9mon-Icon_1013_KAPU.png': 'sinistcha.png',
    }.get(target, target)
    resp = req(url)
    with open(os.path.join('sv-sprites', target), 'wb') as f:
        f.write(resp)


def main() -> int:
    os.makedirs('sv-sprites', exist_ok=True)
    parser = FindImages()
    parser.feed(req(URL).decode())

    with concurrent.futures.ThreadPoolExecutor(4) as exe:
        futures = [exe.submit(_download_one, img) for img in parser.images]
        for _ in concurrent.futures.as_completed(futures):
            print('.', end='', flush=True)
        print()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
