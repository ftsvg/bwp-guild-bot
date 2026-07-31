from dataclasses import asdict

from quart import Blueprint, render_template, session

from apps.web.utils import login_required
from core.api import mojang_client
from core.api.helpers import GuildInfo
from core.database.handlers import WebUserHandler
from core.services import PlayerService, TrackedGuildService

charts_bp = Blueprint("charts", __name__)


@charts_bp.route("/charts")
@login_required
async def charts():
    user_id = session.get("user_id")

    user = WebUserHandler().get_user_by_id(user_id)
    user.username = await mojang_client.get_username(user.uuid)

    guild_info = await GuildInfo.fetch(766)
    xp_chart_data = await PlayerService().get_players_xp_chart_data(guild_info)
    gxp_chart_data = await TrackedGuildService().get_guilds_xp_chart_data()

    serialized_chart_data = [asdict(player_data) for player_data in xp_chart_data]
    serialized_guild_chart_data = [asdict(guild_data) for guild_data in gxp_chart_data]

    return await render_template(
        "charts.html",
        user=user,
        xp_chart=serialized_chart_data,
        guild_chart=serialized_guild_chart_data,
    )
