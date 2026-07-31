from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    token: str = getenv("TOKEN")
    dbhost: str = getenv("DBHOST")
    dbport: int = int(getenv("DBPORT", 3306))
    dbname: str = getenv("DBNAME")
    dbuser: str = getenv("DBUSER")
    dbpass: str = getenv("DBPASS")
    api_key: str = getenv("API_KEY")
    api_key_2: str = getenv("API_KEY_2")
    guild_id: int = int(getenv("GUILD_ID"))


cfg = Config()
