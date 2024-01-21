from __future__ import annotations

import concurrent.futures
import html.parser
import os.path
import time
import urllib.request

URLS = (
    'https://pokemondb.net/pokedex/game/scarlet-violet',
    'https://pokemondb.net/pokedex/game/scarlet-violet/teal-mask',
    'https://pokemondb.net/pokedex/game/scarlet-violet/indigo-disk',
)

REPLACEMENTS = {
    'exeggutor': ('exeggutor', 'exeggutor-alolan'),
    'maushold': ('maushold-family3', 'maushold-family4'),
    'oinkologne': ('oinkologne-male', 'oinkologne-female'),
    'pyroar': ('pyroar-male', 'pyroar-female'),
    'tauros': ('tauros', 'tauros-paldean', 'tauros-aqua', 'tauros-blaze'),

    'diglett': ('diglett', 'diglett-alolan'),
    'dugtrio': ('dugtrio', 'dugtrio-alolan'),

    'grimer': ('grimer', 'grimer-alolan'),
    'muk': ('muk', 'muk-alolan'),

    'geodude': ('geodude', 'geodude-alolan'),
    'graveler': ('graveler', 'graveler-alolan'),
    'golem': ('golem', 'golem-alolan'),

    'sandshrew': ('sandshrew', 'sandshrew-alolan'),
    'sandslash': ('sandslash', 'sandslash-alolan'),

    'vulpix': ('vulpix', 'vulpix-alolan'),
    'ninetales': ('ninetales', 'ninetales-alolan'),

    'slowpoke': ('slowpoke', 'slowpoke-galarian'),
    'slowbro': ('slowbro', 'slowbro-galarian'),
    'slowking': ('slowking', 'slowking-galarian'),
}


class FindImages(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.pokemon: set[str] = set()

    def handle_starttag(
            self,
            tag: str,
            attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != 'a':
            return

        href = dict(attrs).get('href')
        if href is None or not href.startswith('/pokedex/'):
            return

        pokemon = href.split('/')[-1]
        self.pokemon.update(REPLACEMENTS.get(pokemon, (pokemon,)))


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


def _download_one(pokemon: str) -> None:
    url = f'https://img.pokemondb.net/sprites/scarlet-violet/normal/{pokemon}.png'  # noqa: E501
    resp = req(url)
    with open(os.path.join('sv-sprites', f'{pokemon}.png'), 'wb') as f:
        f.write(resp)


def main() -> int:
    os.makedirs('sv-sprites', exist_ok=True)
    parser = FindImages()
    for url in URLS:
        parser.feed(req(url).decode())

    with concurrent.futures.ThreadPoolExecutor(4) as exe:
        futures = [
            exe.submit(_download_one, pokemon)
            for pokemon in sorted(parser.pokemon)
        ]
        for _ in concurrent.futures.as_completed(futures):
            print('.', end='', flush=True)
        print()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
