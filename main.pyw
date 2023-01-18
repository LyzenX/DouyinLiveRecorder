import sys

import src.core.app


def main():
    # 自动识别以命令行还是GUI形式运行
    if sys.stdin and sys.stdin.isatty():
        run_cli()
    else:
        run_gui()


def run_cli():
    src.core.app.init(False)


def run_gui():
    src.core.app.init(True)
    ...


if __name__ == '__main__':
    main()
