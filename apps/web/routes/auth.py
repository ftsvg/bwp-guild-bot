from quart import Blueprint, flash, redirect, request, session

from core.database.handlers import WebSessionHandler

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
async def login():

    token = request.args.get("token")

    if not token:
        return redirect("/")

    session_handler = WebSessionHandler()
    user_id = session_handler.validate_magic_link(token)

    if user_id is None:
        await flash("Invalid or expired login link", "error")
        return redirect("/login")

    session["user_id"] = user_id
    session.permanent = True

    await flash("You are now logged in!", "success")
    return redirect("/dashboard")


@auth_bp.route("/logout")
async def logout():
    session.clear()

    return redirect("/")
