from card import Card

class FieldInfo:
    def __init__(
            self, 
            client_id: int, # 当前玩家的ID
            client_cards: list[Card], # 当前玩家的手牌
            user_names: list[str], # 所有玩家的名字
            users_cards: list[list[Card]], # 所有玩家的牌
            users_cards_num: list[int] # 所有玩家的牌数
            ):
        self.client_id = client_id
        self.client_cards = client_cards
        self.user_names = user_names
        self.users_cards = users_cards
        self.users_cards_num = users_cards_num