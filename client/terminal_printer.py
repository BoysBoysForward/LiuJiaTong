from typing import List
import utils
import sys
import os

def columns(string: str) -> int:
    columns = 0
    for ch in string:
        if '\u4e00' <= ch <= '\u9fff':
            columns += 2 #中文字符占两格
        else:
            columns += 1
    return columns

class TerminalHandler:
    def __init__(self):
        # 终端信息
        self.max_column = os.get_terminal_size().columns - 1
        assert self.max_column >= 4, self.max_column
        self.row = self.column = 0
        self.row_buffer = ""
        self.color = 0
        self.highlight = False
        self.underline = False
        self.blink = False
    
    def update_max_column(self, max_column: int):
        self.max_column = os.get_terminal_size().columns - 1
        self.max_column = min(self.max_column, max_column)
        assert self.max_column >= 4, self.max_column
    
    def move_cursor(self, x: int = 1, y: int = 1):
        print(f"\x1b[{x};{y}H", end='')

    def reset_cursor(self):
        if self.row > 0:
            print(f"\x1b[{self.row}A", end='')
            self.row = 0
        if self.column > 0:
            print(f"\x1b[{self.column}D", end='')
            self.column = 0

    def clear_screen_after_cursor(self):
        print("\x1b[0J", end='')

    def clear_screen_before_cursor(self):
        print("\x1b[1J", end='')

    def clear_screen_all(self):
        print("\x1b[2J", end='')
    
    def reset_font(self):
        print("\x1b[0m", end='')
        self.color = 0
        self.highlight = self.underline = self.blink = False
    
    def set_color(self, color: int):
        print(f"\x1b[{color}m", end='')
        self.color = color

    def set_highlight(self):
        print("\x1b[1m", end='')
        self.highlight = True
    
    def set_underline(self):
        print("\x1b[4m", end='')
        self.underline = True

    def set_blink(self):
        print("\x1b[5m", end='')
        self.blink = True
    
    def flush(self):
        sys.stdout.flush()

    def flush_buffer(self, new_line: bool):
        print(self.row_buffer, end='\n' if new_line else '')
        self.row_buffer = ""
        if new_line:
            self.row += 1
            self.column = 0

    def print_string(self, string:str, new_line: bool):
        assert self.row_buffer == "", self.row_buffer
        for ch in string:
            ch_columns = columns(ch)
            if self.column + ch_columns > self.max_column:
                self.flush_buffer(new_line=True)
            self.row_buffer += ch 
            self.column += ch_columns
        if new_line:
            self.flush_buffer(new_line=True)
        else:
            if self.column == self.max_column:
                self.flush_buffer(new_line=True)
            else:
                self.flush_buffer(new_line=False)

class Sentence:
    """
    打印的切片数据
    :string : 打印的字符串（不带控制序列字符）
    :highlight : 是否要高亮版的字符串
    :color : 如果color为0则打印白色字符，否则打印对应的颜色的字符，控制序列格式串为f'\\x1b[{color}m'
    :blink : 是否需要闪烁字符串
    :underline : 是否需要对字符串添加下划线
    """
    def __init__(self):
        self.string: str = ""
        self.highlight: bool = False
        self.color: int = 0
        self.blink: bool = False
        self.underline: bool = False

    def __str__(self):
        return self.string
    
    def columns(self) -> int:
        return columns(self.string)
    
    def print_font_format(self, th: TerminalHandler):
        if self.highlight:
            th.set_highlight()
        if self.color > 0:
            th.set_color(self.color)
        if self.blink:
            th.set_blink()
        if self.underline:
            th.set_underline()
    # 打印self.string的[l,r)区间
    def print_range(self, th: TerminalHandler, l: int, r: int) -> bool:
        self.print_font_format(th)
        th.print_string(self.string[l:r], new_line=False)
        th.reset_font()
        return r == len(self.string)
    
    def get_printable_pos(self, l: int, now_column: int, max_column: int):
        r = l
        while r < len(self.string):
            ch_columns = columns(self.string[r])
            if now_column + ch_columns > max_column:
                break
            now_column += ch_columns
            r += 1
        return r

Paragraph = List[Sentence]
Chapter = List[Paragraph]
Article = List[Chapter]

def paragraph_columns(paragraph: Paragraph) -> int:
    assert len(paragraph) > 0
    columns = len(paragraph) - 1 #中间用空格隔开
    for sentence in paragraph:
        columns += sentence.columns()
    return columns + 2

def chapter_columns(chapter: Chapter) -> int:
    columns = 0
    for paragraph in chapter:
        columns = max(columns, paragraph_columns(paragraph))
    return columns

def article_columns(article: Article) -> int:
    columns = 0
    for chapter in article:
        columns = max(columns, chapter_columns(chapter))
    return columns

def print_sentence(sentence: Sentence, th: TerminalHandler):
    if sentence.string == "":
        return
    l = 0
    while True:
        r = sentence.get_printable_pos(l, th.column, th.max_column - 1)
        if sentence.print_range(th, l, r):
            break
        l = r
        # 如果之后要打印的字符是汉字(2个空格)，需要额外考虑输出
        if th.column + 1 == th.max_column - 1:
            th.print_string(' ', new_line=False)
        # 行末行首的|
        th.print_string("||", new_line=False)

def print_paragraph(paragraph: Paragraph, th: TerminalHandler):
    assert len(paragraph) > 0
    is_first = True
    for sentence in paragraph:
        if is_first:
            th.print_string('|', new_line=False)
            is_first = False
        else:
            if th.column == th.max_column - 1:
                th.print_string("||", new_line=False)
            assert th.column < th.max_column - 1
            th.print_string(' ', new_line=False)
        print_sentence(sentence, th)
    pad_str = ' ' * (th.max_column - 1 - th.column) + '|'
    th.print_string(pad_str, new_line=True)

def print_chapter(chapter: Chapter, th: TerminalHandler):
    assert len(chapter) > 0
    for paragraph in chapter:
        print_paragraph(paragraph, th)

def print_hline(th: TerminalHandler):
    print_str = '+' + '-' * (th.max_column - 2) + '+'
    th.print_string(print_str, new_line=True)

def print_article(article: Article, th: TerminalHandler):
    print_hline(th)
    for chapter in article:
        print_chapter(chapter, th)
        print_hline(th)