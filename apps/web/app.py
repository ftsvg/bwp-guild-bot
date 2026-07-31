from datetime import datetime, timedelta

from quart import Quart, render_template

from apps.web.routes import auth_bp, charts_bp, dashboard_bp, guild_bp

app = Quart(__name__)

app.secret_key = "12121221"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(charts_bp)
app.register_blueprint(guild_bp)


@app.route("/")
async def index():
    return await render_template("main.html")


@app.template_filter("number")
def number_format(value):
    return f"{value:,}"


@app.template_filter("date")
def format_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")


@app.template_filter("datetime")
def format_datetime(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%d %B %Y, %H:%M %p")


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )
