# app/utils/banner.py
def print_banner_and_github(app=None):
    """
    Prints a stylized banner for Grylli and the GitHub repository URL.

    If the `pyfiglet` library is installed, it prints the "Grylli" text using a
    slant font style with a teal color. If `pyfiglet` is not available, it prints
    a simple text banner.

    Args:
        app (Flask): Optional Flask application instance. If provided and has a
        `config` attribute, it attempts to retrieve the GitHub URL from the
        application's configuration using the key "GITHUB_URL".

    Outputs:
        Prints the Grylli banner and the GitHub repository URL to the console.
    """

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
