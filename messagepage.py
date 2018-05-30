from pagemanagercommand import PageManagerCommand

class MessagePage:
    def __init__(self, msgs):
        self.msgs = msgs

    def up(self):
        pass

    def down(self):
        pass

    def select(self):
        pass

    def back(self):
        pass

    def draw_to_screen(self, screen):
        #screen.clear()
        for i,msg in enumerate(self.msgs):
            screen.write_line(msg, i)