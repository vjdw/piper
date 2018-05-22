class Menu:
    def __init__(self, items):
        self.items = items
        self.parent_menu = None
        self.active_index = 0
        self.viewtop_index = 0

class MenuItem:
    def __init__(self, text, method="", target=""):
        self.text = text
        self.active = False
        self.method = method
        self.target = target
        self.child_menu = None