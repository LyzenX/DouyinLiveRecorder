import sys

import dylr.core.app as app


def main():
    # 自动识别以命令行还是GUI形式运行
    if sys.stdin and sys.stdin.isatty():
        run_cli()
    else:
        run_gui()
    # run_cli()


def run_cli():
    app.init(False)


def run_gui():
    app.init(True)
    ...


if __name__ == '__main__':
    main()
