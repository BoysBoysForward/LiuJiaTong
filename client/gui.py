import copy
import tkinter as tk
import threading
from tkinter import PhotoImage
from PIL import Image, ImageTk

import logger
from card import Card, Suits
from FieldInfo import FieldInfo
import utils
import queue

# 创建一个线程安全的队列，用于传递用户选中的卡牌
card_queue = queue.Queue()

# users_name = []
# my_cards = []
DEFAULT_WINDOW_WIDTH = 1440
DEFAULT_WINDOW_HEIGHT = 810

class GUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.field_info = None
        self.selected_card_flag = [False] * 36
        self.my_card_labels = []

def update_gui(info: FieldInfo):
    logger.info("update gui")   
    gui_obj.field_info = copy.deepcopy(info)
    gui_obj.root.event_generate("<<UpdateEvent>>")

def on_resize(event):
    # 获取窗口的宽度
    window_width = event.width
    window_height = event.height

    global label1, label2, label3, label4, label5
    label1_x = window_width - label1.winfo_width()
    label2_x = window_width - label2.winfo_width()
    label3_y = window_height + label3.winfo_height()
    label4_x = window_width + label4.winfo_width()
    label5_x = window_width + label5.winfo_width()
    # print(f"Lable 1 width: {label1.winfo_width()}. Lable 2 width: {label2.winfo_width()}. Lable 3 height: {label3.winfo_height()}. Lable 4 width: {label4.winfo_width()}. Lable 5 width: {label5.winfo_width()}")

    # 更新Label的位置
    label1.place(x=label1_x, y=400)
    label2.place(x=label2_x, y=200)
    label3.place(x=window_width * 0.3, y=label3_y + 50)
    label4.place(x=label4_x, y=200)
    label5.place(x=label5_x, y=400)


def init_gui():
    logger.info("init gui")
    def start_gui():
        # 用Tkinter初始化界面
        root = tk.Tk()
        root.title("LiuJiaTong")
        root.geometry("1440x810")
        root.bind("<<UpdateEvent>>", handle_update_event)
        # root.bind('<Configure>', on_resize) # 绑定窗口大小变化事件
        global gui_obj
        gui_obj = GUI(root)
        root.mainloop()

    # 启动 GUI 线程
    gui_thread = threading.Thread(target=start_gui)
    gui_thread.daemon = True # 设置为守护线程，这样主程序退出时 GUI 也会退出
    gui_thread.start()

def handle_update_event(event):
    logger.info("handle update event")
    draw_user_names()
    draw_user_cards()
    draw_buttons()

def card_to_photo(card: Card) -> ImageTk.PhotoImage:
    # 卡牌素材来源：https://gitcode.com/open-source-toolkit/77d38/?utm_source=tools_gitcode&index=bottom&type=card&
    if card.suit == Suits.empty:
        image_path = "client/images/JOKER-B.png" if card.value == 16 else "client/images/JOKER-A.png"
    elif card.value > 10:
        image_path = "client/images/" + card.suit.value + utils.int_to_str(card.value) + ".png"
    else:
        image_path = "client/images/" + card.suit.value + str(card.value) + ".png"
    image = Image.open(image_path) # 打开图片

    # 等比例缩小图片至高度为100像素
    target_height = 100
    width, height = image.size
    scale = target_height / height
    new_width = int(width * scale) # 71
    image = image.resize((new_width, target_height))
    return ImageTk.PhotoImage(image)

def draw_one_card(card: Card, x: int, y: int) -> tk.Label:
    # 在 GUI 中显示图片
    photo = card_to_photo(card)
    label = tk.Label(gui_obj.root, image=photo) # 这里的image参数是必须指定的，与下一行不冲突
    label.image = photo
    label.place(x=x, y=y)
    label.bind("<Button-1>", on_my_card_click)
    return label

def on_my_card_click(event):
    # 获取当前Label的x和y坐标
    label = event.widget
    current_x = label.winfo_x()
    current_y = label.winfo_y()
    
    # 遍历my_card_labels，找到对应的索引，然后判断是否选中了
    for i in range(len(gui_obj.my_card_labels)):
        if gui_obj.my_card_labels[i] != label:
            continue

        if gui_obj.selected_card_flag[i]:
            # 将Label向下移动20个单位
            new_y = current_y + 20
            label.place(x=current_x, y=new_y)
        else:
            # 将Label向上移动20个单位
            new_y = current_y - 20
            label.place(x=current_x, y=new_y)

        gui_obj.selected_card_flag[i] = not gui_obj.selected_card_flag[i]

def grid_one_card(card: Card, row: int, column: int):
    photo = card_to_photo(card)
    label = tk.Label(gui_obj.root, image=photo)
    label.image = photo
    label.grid(row=row, column=column)

def draw_background(x: int, y: int, anchor: str='nw'):
    image = Image.open("client/images/Background.png") # 打开图片

    # 等比例缩小图片至高度为75像素
    target_height = 100
    width, height = image.size
    scale = target_height / height
    new_width = int(width * scale)
    image = image.resize((new_width, target_height))

    photo = ImageTk.PhotoImage(image)
    label = tk.Label(gui_obj.root, image=photo) # 这里的image参数是必须指定的，与下一行不冲突
    label.image = photo
    label.place(x=x, y=y, anchor=anchor)
    
def draw_my_cards():
    # Draw my cards
    # 36张牌的宽度是71+35*20=771
    for i in range(len(gui_obj.field_info.client_cards)):
        label = draw_one_card(gui_obj.field_info.client_cards[i], (DEFAULT_WINDOW_WIDTH - 1121) / 2 + i * 30 - 80, DEFAULT_WINDOW_HEIGHT - 140)
        gui_obj.my_card_labels.append(label)

def draw_left_cards():
    # Draw other player cards with Background.png
    left_text_1 = f"剩{gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 4) % 6]}张"
    left_label_1 = tk.Label(gui_obj.root, text=left_text_1, font=("Arial", 20))
    left_label_1.place(x=20, y=DEFAULT_WINDOW_HEIGHT / 4 + 40, anchor='nw')
    draw_background(40, DEFAULT_WINDOW_HEIGHT / 4 + 80)
    
    left_text_2 = f"剩{gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 5) % 6]}张"
    left_label_2 = tk.Label(gui_obj.root, text=left_text_2, font=("Arial", 20))
    left_label_2.place(x=20, y=DEFAULT_WINDOW_HEIGHT / 2 + 40, anchor='nw')
    draw_background(40, DEFAULT_WINDOW_HEIGHT / 2 + 80)

def draw_right_cards():
    # Draw other player cards with Background.png
    right_text_1 = f"剩{gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 1) % 6]}张"
    right_label_1 = tk.Label(gui_obj.root, text=right_text_1, font=("Arial", 20))
    right_label_1.place(x=DEFAULT_WINDOW_WIDTH - 20, y=DEFAULT_WINDOW_HEIGHT / 4 + 40, anchor='ne')
    draw_background(DEFAULT_WINDOW_WIDTH - 40, DEFAULT_WINDOW_HEIGHT / 4 + 80, "ne")
    
    right_text_2 = f"剩{gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 2) % 6]}张"
    right_label_2 = tk.Label(gui_obj.root, text=right_text_2, font=("Arial", 20))
    right_label_2.place(x=DEFAULT_WINDOW_WIDTH - 20, y=DEFAULT_WINDOW_HEIGHT / 2 + 40, anchor='ne')
    draw_background(DEFAULT_WINDOW_WIDTH - 40, DEFAULT_WINDOW_HEIGHT / 2 + 80, "ne")

def draw_top_cards():
    top_text = f"剩{gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 3) % 6]}张"
    top_label = tk.Label(gui_obj.root, text=top_text, font=("Arial", 20))
    top_label.place(x=DEFAULT_WINDOW_WIDTH - 80, y=80, anchor='ne')
    for i in range(gui_obj.field_info.users_cards_num[(gui_obj.field_info.client_id + 3) % 6]):
        draw_background((DEFAULT_WINDOW_WIDTH - 1121) / 2 + i * 30 - 80, 40)

def draw_user_cards():
    draw_my_cards()
    draw_left_cards()
    draw_right_cards()
    draw_top_cards()

def draw_user_names():
    print("draw user names")
    print(gui_obj.field_info.user_names)

    # 从下一个玩家开始绘制名字，两个右侧，一个顶部，两个左侧
    global label1, label2, label3, label4, label5
    label1 = tk.Label(gui_obj.root, text=gui_obj.field_info.user_names[(gui_obj.field_info.client_id + 1) % 6], font=("Arial", 20))
    label1.place(x=DEFAULT_WINDOW_WIDTH - 20, y=DEFAULT_WINDOW_HEIGHT / 2, anchor='ne')
    label2 = tk.Label(gui_obj.root, text=gui_obj.field_info.user_names[(gui_obj.field_info.client_id + 2) % 6], font=("Arial", 20))
    label2.place(x=DEFAULT_WINDOW_WIDTH - 20, y=DEFAULT_WINDOW_HEIGHT / 4, anchor='ne')
    label3 = tk.Label(gui_obj.root, text=gui_obj.field_info.user_names[(gui_obj.field_info.client_id + 3) % 6], font=("Arial", 20))
    label3.place(x=DEFAULT_WINDOW_WIDTH / 2, y=0, anchor='n')
    label4 = tk.Label(gui_obj.root, text=gui_obj.field_info.user_names[(gui_obj.field_info.client_id + 4) % 6], font=("Arial", 20))
    label4.place(x=20, y=DEFAULT_WINDOW_HEIGHT / 4, anchor='nw')
    label5 = tk.Label(gui_obj.root, text=gui_obj.field_info.user_names[(gui_obj.field_info.client_id + 5) % 6], font=("Arial", 20))
    label5.place(x=20, y=DEFAULT_WINDOW_HEIGHT / 2, anchor='nw')

def draw_buttons():
    reset_button = tk.Button(gui_obj.root, text="重置", width=18, command=on_reset_button_click)
    reset_button.place(x=DEFAULT_WINDOW_WIDTH - 30, y=DEFAULT_WINDOW_HEIGHT - 150, anchor='ne')

    confirm_button = tk.Button(gui_obj.root, text="确定", width=18, command=on_confirm_button_click)
    confirm_button.place(x=DEFAULT_WINDOW_WIDTH - 30, y=DEFAULT_WINDOW_HEIGHT - 100, anchor='ne')

    skip_button = tk.Button(gui_obj.root, text="跳过", width=18, command=on_skip_button_click)
    skip_button.place(x=DEFAULT_WINDOW_WIDTH - 30, y=DEFAULT_WINDOW_HEIGHT - 50, anchor='ne')
    
def on_reset_button_click():
    # 遍历label
    for label in gui_obj.my_card_labels:
        # 撤销所有选中的牌
        label_index = gui_obj.my_card_labels.index(label)
        if gui_obj.selected_card_flag[label_index]:
            label.place(x=label.winfo_x(), y=label.winfo_y() + 20)
            gui_obj.selected_card_flag[label_index] = False

def on_confirm_button_click():
    # 检查卡牌合法性
    
    # 抽出卡牌

    # 重绘UI
    pass

def on_skip_button_click():
    # 重置卡牌
    on_reset_button_click()

    # 告知服务器

