import random
import utils
import threading
import logger
from game_vars import gvar
from state_machine import GameState, GameStateMachine

# 初始化牌
def init_cards():
    all_cards = []
    # 3~10,J,Q,K,A,2
    for i in range(3, 16):
        for _ in range(16):
            all_cards.append(i)
    # Jockers
    for i in range(16, 18):
        for _ in range(4):
            all_cards.append(i)
    random.shuffle(all_cards)

    for i in range(0, 6):
        user_cards = sorted([all_cards[j] for j in range(i, len(all_cards), 6)])
        gvar.users_cards[i] = [utils.int_to_str(x) for x in user_cards]

'''
判断游戏是否结束
返回值
0 表示没有结束 
1, -1 分别表示偶数队获胜,双统
2, -2 分别表示奇数队获胜,双统
'''
def if_game_over():
    # 没有头科肯定没有结束
    if gvar.head_master == -1:
        return 0
    # 根据各队分数以及逃出人数判断
    for i in range(2):
        if gvar.team_score[i] >= 200 and gvar.team_out[i] == 3 and gvar.team_out[1 - i] == 0:
            return -(i + 1)
        elif (gvar.team_score[i] >= 200 and gvar.team_out[1 - i] != 0) or gvar.team_out[i] == 3:
            return i + 1
    return 0

# 下一位玩家出牌
def set_next_player():
    gvar.now_player = (gvar.now_player + 1) % 6
    while gvar.users_finished[gvar.now_player]:
        gvar.now_player = (gvar.now_player + 1) % 6

def get_next_turn():
    assert gvar.game_lock.locked()
    # skip
    if gvar.users_played_cards[gvar.now_player][0] == 'F':
        gvar.users_played_cards[gvar.now_player].clear()
    else:
        gvar.last_player = gvar.now_player
    
    # 此轮逃出，更新队伍信息、头科，判断游戏是否结束
    if len(gvar.users_cards[gvar.now_player]) == 0:
        gvar.team_out[gvar.now_player % 2] += 1
        if gvar.head_master == -1:
            gvar.head_master = gvar.now_player
            for i in range(6):
                if i % 2 == gvar.head_master % 2:
                    gvar.team_score[i % 2] += gvar.users_score[i]
        # 若队伍有头科，就不需要累加，没有则累加
        elif gvar.head_master % 2 != gvar.now_player % 2:
            gvar.team_score[gvar.now_player % 2] += gvar.users_score[gvar.now_player]

        gvar.game_over = if_game_over()
    
    # 更新一下打牌的user
    set_next_player()
    # 玩家是否打完所有的牌
    # 不在打完之后马上结算是因为玩家的分没拿
    # 考虑到有多个人同时打完牌的情况，得用循环
    while len(gvar.users_cards[gvar.now_player]) == 0 \
            and gvar.last_player != gvar.now_player:
        gvar.users_finished[gvar.now_player] = True
        gvar.users_played_cards[gvar.now_player].clear()
        set_next_player()
    
    # 一轮结束，统计此轮信息
    if gvar.last_player == gvar.now_player:
        # 统计用户分数
        gvar.users_score[gvar.now_player] += gvar.now_score
        # 队伍有头科，此轮分数直接累加到队伍分数中
        if gvar.head_master != -1 and gvar.now_player % 2 == gvar.head_master % 2:
            gvar.team_score[gvar.now_player % 2] += gvar.now_score
        # 若是刚好此轮逃出，此轮分数也直接累加到队伍分数中
        elif len(gvar.users_cards[gvar.now_player]) == 0:
            gvar.team_score[gvar.now_player % 2] += gvar.now_score
        # 判断游戏是否结束
        gvar.game_over = if_game_over()
        # 初始化场上分数
        gvar.now_score = 0
        # 如果刚好在此轮逃出，第一个出牌的人就要改变
        if len(gvar.users_cards[gvar.now_player]) == 0:
            gvar.users_finished[gvar.now_player] = True
            gvar.users_played_cards[gvar.now_player].clear()
            set_next_player()
            gvar.last_player = gvar.now_player

    # 清除当前玩家的场上牌
    gvar.users_played_cards[gvar.now_player].clear()

class Manager(GameStateMachine):
    def game_start(self): 
        if self.static_user_order:
            pass
        else:
            # 随机出牌顺序
            with gvar.users_info_lock:
                random.shuffle(gvar.users_info)
        with gvar.game_lock:
            gvar.init_game_env()
            init_cards()  # 初始化牌并发牌
    def game_over(self): 
        gvar.init_global_env()
    def onlooker_register(self): 
        raise RuntimeError("unsupport state")
    def next_turn(self): 
        with gvar.game_lock:
            get_next_turn()
    def send_field_info(self): 
        raise RuntimeError("unsupport state")
    def send_round_info(self): 
        # 会在send_round_info_sync处放掉
        gvar.onlooker_lock.acquire()
        # barrier要考虑自己
        gvar.onlooker_barrier = threading.Barrier(gvar.onlooker_number + 1)
        gvar.onlooker_event.set()
        gvar.onlooker_event.clear()
        gvar.onlooker_barrier.wait()
    def recv_player_info(self): 
        raise RuntimeError("unsupport state")
    def init_sync(self): 
        gvar.game_init_barrier.wait()
        gvar.game_init_barrier.reset()
    def onlooker_sync(self): 
        raise RuntimeError("unsupport state")
    def game_start_sync(self): 
        gvar.game_start_barrier.wait()
        gvar.game_start_barrier.reset()
        assert gvar.onlooker_lock.locked()
        # 在游戏还没开始前由manager将其锁住
        gvar.onlooker_lock.release()
    def send_round_info_sync(self): 
        gvar.send_round_info_barrier.wait()
        gvar.send_round_info_barrier.reset()
        # 如果游戏还没结束，放掉send_round_info设置的锁
        # 否则一直保持锁直到下一局游戏开始(game_start_sync)
        if self.__game_over == 0:
            gvar.onlooker_lock.release()
    def recv_player_info_sync(self): 
        gvar.recv_player_info_barrier.wait()
        gvar.recv_player_info_barrier.reset()
    def next_turn_sync(self): 
        gvar.next_turn_barrier.wait()
        gvar.next_turn_barrier.reset()
        # 这里放松了条件，因为在下一个同步点之前数据是只读的
        with gvar.game_lock:
            self.__game_over = gvar.game_over
    
    # 这个代码太tm抽象了，看我画的drawio的图，为了支持断线重连真不容易……
    def get_next_state(self) -> bool:
        if self.state == GameState.init:
            self.state = GameState.init_sync
        elif self.state == GameState.init_sync:
            self.state = GameState.game_start
        elif self.state == GameState.game_start:
            self.state = GameState.game_start_sync
        elif self.state == GameState.game_start_sync:
            self.state = GameState.send_round_info
        elif self.state == GameState.send_round_info:
            self.state = GameState.send_round_info_sync
        elif self.state == GameState.send_round_info_sync:
            if self.__game_over != 0:
                self.state = GameState.game_over
            else:
                self.state = GameState.recv_player_info_sync
        elif self.state == GameState.recv_player_info_sync:
            self.state = GameState.next_turn
        elif self.state == GameState.next_turn:
            self.state = GameState.next_turn_sync
        elif self.state == GameState.next_turn_sync:
            self.state = GameState.send_round_info
        elif self.state == GameState.game_over:
            self.state = GameState.init_sync
        else:
            raise RuntimeError("unsupport state")
        logger.info(f"manager: {self.state}")
        return True

    def __init__(self, static_user_order):
        super().__init__()

        gvar.init_global_env()

        self.__game_over = 0
        self.static_user_order = static_user_order
