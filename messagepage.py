class MessagePage:
    def __init__(self, msgs):
        self.msgs = msgs

    def draw_to_screen(self, screen):
        #screen.clear()
        for i,msg in enumerate(self.msgs):
            screen.write_line(msg, i)