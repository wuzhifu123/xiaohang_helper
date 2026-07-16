"""
小航 · 郑州航院校园信息助手 - EXE 启动入口
运行后自动启动 Streamlit 服务器并打开浏览器
"""
import sys
import os
from streamlit.web import cli as stcli


def main():
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        os.chdir(base_dir)
        sys.path.insert(0, base_dir)
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