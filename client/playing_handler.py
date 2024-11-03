import os
import sys
import time
import logger
import utils
from enum import Enum, auto
from playingrules import if_input_legal
from terminal_printer import *
import sound
from card import Card

class SpecialInput(Enum):
    left_arrow = auto(),
    right_arrow = auto(),
    backspace = auto(),

class InputException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class PlayingTerminalHandler(TerminalHandler):
    def __init__(self):
        super().__init__()
        # 用户打牌信息
        self.new_played_cards = []
        self.cursor = 0
        self.err = ""
    
    def print(self):
        # 恢复光标并清理所有的下面的屏幕数据
        self.reset_cursor()
        self.clear_screen_after_cursor()
        # 打印信息
        self.print_string("".join(self.new_played_cards), new_line=True)
        self.print_string(self.err, new_line=False)
        # 恢复光标
        self.reset_cursor()
        # 再输出一遍直到cursor位置
        self.print_string("".join(self.new_played_cards[0:self.cursor]), new_line=False)
        # 最后刷新print的缓冲区
        self.flush()

g_terminal_handler = None
g_tcp_handler = None
HANG_OUT_COUNTER = 10
g_user_hang_out_counter = HANG_OUT_COUNTER

def check_user_hang_out():
    global g_user_hang_out_counter
    if g_user_hang_out_counter > 0:
        g_user_hang_out_counter -= 1
        if g_user_hang_out_counter == 0:
            sound.playsound("ahoo", True, None)

def reset_user_hang_out():
    global g_user_hang_out_counter
    g_user_hang_out_counter = HANG_OUT_COUNTER

def clear_user_hang_out():
    global g_user_hang_out_counter
    g_user_hang_out_counter = 0

def wait_for_input():
    TCP_COUNTER = 20
    check_tcp_counter = TCP_COUNTER
    while check_have_input() is False:
        if check_tcp_counter == 0:
            g_tcp_handler.send_playing_heartbeat(finished=False)
            check_user_hang_out()
            check_tcp_counter = TCP_COUNTER
        check_tcp_counter -= 1
        time.sleep(0.05)
    clear_user_hang_out()

if os.name == 'posix':
    # linux & mac
    import select
    def check_have_input() -> bool:
        return select.select([sys.stdin], [], [], 0) != ([], [], [])

    def read_byte(if_blocking: bool) -> str:
        if if_blocking:
            wait_for_input()
        else:
            if check_have_input() is False:
                raise InputException('(非阻塞输入)')
        return chr(sys.stdin.buffer.read1(1)[0])

    def read_direction(if_blocking: bool):
        if read_byte(if_blocking) != '[':
            raise InputException('(非法输入)')
        else:
            dir = read_byte(if_blocking)
            if dir == 'D':
                return SpecialInput.left_arrow
            elif dir == 'C':
                return SpecialInput.right_arrow
            else:
                raise InputException('(非法输入)')

    def read_input(if_blocking: bool):
        fst_byte = read_byte(if_blocking).upper()
        if fst_byte == '\x1b':
            # 判断是否是左右方向键
            return read_direction(if_blocking)
        elif fst_byte == '\x7f':
            return SpecialInput.backspace
        elif fst_byte in ['\n', '\t', 'C', 'F']:
            return fst_byte
        elif utils.str_to_int(fst_byte) != -1:
            return fst_byte
        else:
            raise InputException('(非法输入)')
    
elif os.name == 'nt':
    # windows
    from msvcrt import getch, kbhit
    def check_have_input():
        return kbhit() != 0

    def read_byte(if_blocking: bool) -> str:
        if if_blocking:
            wait_for_input()
        else:
            if check_have_input() is False:
                raise InputException('(非阻塞输入)')
        return chr(getch()[0])
        
    def read_direction(if_blocking: bool):
        dir = read_byte(if_blocking)
        if dir == 'K':
            return SpecialInput.left_arrow
        elif dir == 'M':
            return SpecialInput.right_arrow
        else:
            raise InputException('(非法输入)')

    def read_input(if_blocking: bool):
        fst_byte = read_byte(if_blocking)
        if fst_byte == '\xe0':
            return read_direction(if_blocking)
        fst_byte = fst_byte.upper()
        if fst_byte == '\x03':
            utils.fatal("Keyboard Interrupt")
        elif fst_byte == '\x08':
            return SpecialInput.backspace
        elif fst_byte in ['\r', '\t', 'C', 'F']:
            return fst_byte
        elif utils.str_to_int(fst_byte) != -1:
            return fst_byte
        else:
            raise InputException('(非法输入)')

g_input_buffer = []
def prepare_input_buffer():
    global g_input_buffer
    try:
        g_input_buffer = []
        while True:
            g_input_buffer.append(read_input(if_blocking=False))
    except InputException:
        g_input_buffer = [x for x in g_input_buffer if x not in ['\r', '\n']]
        import logger
        logger.info(f"{g_input_buffer}")

def read_input_buffer():
    global g_input_buffer
    if len(g_input_buffer) > 0:
        input = g_input_buffer[0]
        g_input_buffer = g_input_buffer[1:]
        return input
    else:
        return None

def get_input():
    input = read_input_buffer()
    if input is not None:
        return input
    return read_input(if_blocking=True)

def read_userinput(client_cards):
    th = g_terminal_handler
    while True:
        assert(th.cursor <= len(th.new_played_cards))
        end_input = False
        try:
            input = get_input()
            if input == SpecialInput.left_arrow:
                if th.cursor > 0:
                    th.cursor -= 1
            elif input == SpecialInput.right_arrow:
                if th.cursor < len(th.new_played_cards):
                    th.cursor += 1
            elif input == SpecialInput.backspace:
                if th.cursor > 0:
                    th.new_played_cards = th.new_played_cards[:th.cursor - 1] + th.new_played_cards[th.cursor:]
                    th.cursor -= 1
            elif input in ['\n', '\r']:
                end_input = True
            elif input == '\t':
                if th.new_played_cards == ['F']:
                    continue
                if th.cursor > 0:
                    fill_char = th.new_played_cards[th.cursor - 1]
                    used_num = th.new_played_cards.count(fill_char)
                    total_num = client_cards.count(fill_char)
                    fill_num = total_num - used_num
                    assert (fill_num >= 0)
                    th.new_played_cards = th.new_played_cards[:th.cursor] + fill_num * [fill_char] + th.new_played_cards[th.cursor:]
                    th.cursor += fill_num
            elif input == 'F':
                th.new_played_cards = ['F']
                th.cursor = 1
            elif input == 'C':
                th.new_played_cards = []
                th.cursor = 0
            else:
                assert(th.new_played_cards.count(input) <= client_cards.count(input))
                if th.new_played_cards.count(input) == client_cards.count(input):
                    raise InputException('(你打出的牌超过上限了)')
                if th.new_played_cards == ['F']:
                    th.new_played_cards = []
                    th.cursor = 0
                th.new_played_cards = th.new_played_cards[:th.cursor] + [input] + th.new_played_cards[th.cursor:]
                th.cursor += 1
        except InputException as err:
            th.err = err.args[0]
        else:
            th.err = ""
        finally:
            th.print()
        if end_input:
            break
        assert(th.new_played_cards == ['F'] or th.new_played_cards.count('F') == 0)
    return th.new_played_cards

# client_cards: 用户所持卡牌信息
# last_player: 最后打出牌的玩家
# client_player: 客户端正在输入的玩家
# users_played_cards: 场上所有牌信息
# tcp_handler: 客户端句柄，用于检测远端是否关闭了
def playing(
    client_cards : list[Card], # 用户所持卡牌信息
    last_player  : int,        # 最后打出牌的玩家
    client_player: int,        # 客户端正在输入的玩家
    users_played_cards: list[Card], # 场上所有牌信息
    tcp_handler # 客户端句柄，用于检测远端是否关闭了
):
    logger.info(f"playing(client_cards: {client_cards}, last_player: {last_player}, client_player: {client_player}, users_played_cards: {users_played_cards})")
    global g_tcp_handler
    g_tcp_handler = tcp_handler
    reset_user_hang_out()
    prepare_input_buffer()
    print('请输入要出的手牌(\'F\'表示跳过):')
    global g_terminal_handler
    g_terminal_handler = PlayingTerminalHandler()

    new_played_cards = []
    new_score = 0

    logger.info(f"last played: {users_played_cards[last_player] if last_player != client_player else None}")
    while True:
        new_played_cards = read_userinput(client_cards)
        _if_input_legal, new_score = if_input_legal(
            [utils.str_to_int(c) for c in new_played_cards],
            [utils.str_to_int(c) for c in client_cards],
            [utils.str_to_int(c) for c in users_played_cards[last_player]]
                if last_player != client_player else None
        )
        if _if_input_legal:
            logger.info(f"now play: {new_played_cards}")
            tcp_handler.send_playing_heartbeat(finished=True)
            break
        g_terminal_handler.err = '(非法牌型)'
        g_terminal_handler.print()
    
    return new_played_cards, new_score