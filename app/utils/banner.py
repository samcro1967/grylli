# app/utils/banner.py
def print_banner_and_github(app=None):
    try:
        from pyfiglet import Figlet

        teal = "\033[38;2;0;124;130m"
        reset = "\033[0m"
        print(teal + Figlet(font="slant").renderText("Grylli") + reset)
    except ImportError:
        print("🐛 Grylli")
    github_url = None
    if app and hasattr(app, "config"):
        github_url = app.config.get("GITHUB_URL")
    print(f"📦 GitHub: {github_url or '[No Repo URL Found]'}")
