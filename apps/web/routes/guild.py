from dataclasses import asdict, dataclass

from quart import Blueprint, render_template, session

from apps.web.utils import login_required
from core.api import mojang_client
from core.api.helpers import GuildInfo
from core.database.handlers import GuildTrackerHandler, WebUserHandler
from core.services import GuildService, PlayerService, TrackedGuildService

guild_bp = Blueprint("guild", __name__)


@dataclass(slots=True)
class GuildDetails:
    id: int
    name: str
    desc: str
    original_owner: str
    creation_time: int
    gxp: int
    member_count: int


@guild_bp.route("/guilds")
@login_required
async def guilds():
    user_id = session.get("user_id")

    user = WebUserHandler().get_user_by_id(user_id)
    user.username = await mojang_client.get_username(user.uuid)

    tracked_guilds = await TrackedGuildService().get_tracked_guilds()

    return await render_template(
        "guilds.html", user=user, tracked_guilds=tracked_guilds
    )


@guild_bp.route("/guilds/<int:guild_id>")
@login_required
async def check(guild_id):
    user_id = session.get("user_id")

    user = WebUserHandler().get_user_by_id(user_id)
    user.username = await mojang_client.get_username(user.uuid)

    guild_info = await GuildInfo.fetch(guild_id)

    guild_data = GuildDetails(
        id=guild_info.id,
        name=guild_info.name,
        desc=guild_info.description,
        original_owner=await mojang_client.get_username(guild_info.owner_uuid),
        creation_time=guild_info.creation_time,
        gxp=guild_info.xp,
        member_count=guild_info.member_count,
    )

    xp_chart_data = await PlayerService().get_players_xp_chart_data(guild_info)
    serialized_chart_data = [asdict(player_data) for player_data in xp_chart_data]

    daily_gained_xp = GuildService(guild_info).get_daily_gained_gxp()
    weekly_gained_xp = GuildService(guild_info).get_weekly_gained_gxp()

    guild_members = await GuildService(guild_info).get_guild_members()
    guild_logs = GuildTrackerHandler().get_logs(guild_id=guild_id, limit=10)

    return await render_template(
        "guild_check.html",
        user=user,
        guild_data=guild_data,
        xp_chart=serialized_chart_data,
        daily_gxp=daily_gained_xp,
        weekly_gxp=weekly_gained_xp,
        guild_members=guild_members,
        guild_logs=guild_logs,
    )
