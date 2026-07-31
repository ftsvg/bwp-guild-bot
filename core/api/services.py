from os import getenv

from dotenv import load_dotenv

from .cache import Cache
from .mojang import MojangClient
from .voxyl import VoxylClient

load_dotenv()

cache = Cache(
    redis_host=getenv("REDIS_HOST"),
    redis_port=int(getenv("REDIS_PORT")),
    password=getenv("REDIS_PASSWORD"),
)

mojang_client = MojangClient(cache=cache)
voxyl_client = VoxylClient(cache=cache)
