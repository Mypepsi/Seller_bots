from typing import (
    Dict,
    Mapping,
)

from bots_libraries.steampy.steam_auth.abstract import CookieStorageAbstract


class BaseCookieStorage(CookieStorageAbstract):

    def __init__(self):
        self.cookies: Dict[str, Mapping[str, Mapping[str, str]]] = {}

    async def set(self, login: str, cookies: Mapping[str, Mapping[str, str]]) -> None:
        self.cookies[login] = cookies

    async def get(self, login: str, domain: str) -> Mapping[str, str]:
        cookies = self.cookies.get(login)
        if not cookies:
            return {}
        return cookies.get(domain, {})
