import copy
import tkinter as tk
import threading
from tkinter import PhotoImage
from PIL import Image, ImageTk

import logger
from card import Card, Suits
import utils

# users_name = []
# my_cards = []

def update_gui(identity: int, names: list[str], client_cards: list[Card]):
    logger.info("update gui")
    global client_id
    client_id = identity
    global users_name
    users_name = copy.deepcopy(names)
    global my_cards
    my_cards = copy.deepcopy(client_cards)
    global root
    root.event_generate("<<UpdateEvent>>")
    root.event_generate("<Configure>")

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
        global root
        root = tk.Tk()
        root.title("LiuJiaTong")
        root.geometry("1000x600")
        root.bind("<<UpdateEvent>>", handle_update_event)
        root.bind('<Configure>', on_resize) # 绑定窗口大小变化事件
        root.mainloop()

    # 启动 GUI 线程
    gui_thread = threading.Thread(target=start_gui)
    gui_thread.daemon = True # 设置为守护线程，这样主程序退出时 GUI 也会退出
    gui_thread.start()

def handle_update_event(event):
    logger.info("handle update event")

    draw_user_names()

    # Draw my cards
    for i in range(len(my_cards)):
        draw_one_card(my_cards[i], 115 + i * 20, 450)

    # Draw other player cards with Background.png
    draw_left_cards()

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

def draw_one_card(card: Card, x: int, y: int):
    # 在 GUI 中显示图片
    photo = card_to_photo(card)
    label = tk.Label(root, image=photo) # 这里的image参数是必须指定的，与下一行不冲突
    label.image = photo
    label.place(x=x, y=y)

def grid_one_card(card: Card, row: int, column: int):
    photo = card_to_photo(card)
    label = tk.Label(root, image=photo)
    label.image = photo
    label.grid(row=row, column=column)

def draw_left_cards():
    pass

def draw_right_cards():
    pass

def draw_top_cards():
    pass

def draw_user_names():
    print("draw user names")
    global users_name
    global client_id

    print(users_name)
    # 从下一个玩家开始绘制名字，两个右侧，一个顶部，两个左侧
    global label1, label2, label3, label4, label5
    label1 = tk.Label(root, text=users_name[(client_id + 1) % 6], font=("Arial", 20))
    label1.place(x=900, y=400, anchor='w')
    label2 = tk.Label(root, text=users_name[(client_id + 2) % 6], font=("Arial", 20))
    label2.place(x=900, y=200, anchor='w')
    label3 = tk.Label(root, text=users_name[(client_id + 3) % 6], font=("Arial", 20))
    label3.place(x=200, y=0, anchor='w')
    label4 = tk.Label(root, text=users_name[(client_id + 4) % 6], font=("Arial", 20))
    label4.place(x=0, y=200, anchor='w')
    label5 = tk.Label(root, text=users_name[(client_id + 5) % 6], font=("Arial", 20))
    label5.place(x=0, y=400, anchor='w')
