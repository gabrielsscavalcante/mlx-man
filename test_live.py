import sys, termios, tty, time
from rich.live import Live
from rich.text import Text

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

with Live(Text("Hello"), screen=True, refresh_per_second=4) as live:
    # block on read
    # if you resize while blocking, does Live redraw?
    pass
