from functools import wraps

from quart import redirect, session

from core.database.handlers import WebUserHandler


def login_required(view):
    @wraps(view)
    async def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if user_id is None:
            return redirect("/")

        handler = WebUserHandler()
        try:
            user = handler.get_user_by_id(user_id)
        except Exception:
            session.clear()
            return redirect("/")

        if user is None:
            session.clear()
            return redirect("/")

        return await view(*args, **kwargs)

    return wrapped_view
