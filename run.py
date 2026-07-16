"""
小航 · 郑州航院校园信息助手 - EXE 启动入口
运行后自动启动 Streamlit 服务器并打开浏览器
"""
import sys
import os
from streamlit.web import cli as stcli


def main():
    # 获取 try.py 的绝对路径（和 exe 同目录）
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的环境
        base_dir = sys._MEIPASS
        # 关键：改变工作目录到解压目录，让 try.py 中的 Path("data") 能找到 data 文件夹
        os.chdir(base_dir)
        # 把解压目录加入 Python 模块搜索路径，让 try.py 能 import prompts
        sys.path.insert(0, base_dir)
    else:
        # 开发环境
        base_dir = os.path.dirname(os.path.abspath(__file__))

    app_path = os.path.join(base_dir, "try.py")

    # 模拟 streamlit run try.py 命令
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
