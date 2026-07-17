import sys
import os
from streamlit.web import cli as stcli


def main():
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        os.chdir(base_dir)
        sys.path.insert(0, base_dir)
        app_path = os.path.join(base_dir, "src", "app.py")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(base_dir, "app.py")

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=false",
    ]

    stcli.main()


if __name__ == "__main__":
    main()