class PageManagerCommand:
    redraw_command = "cmd-redraw"
    close_command = "cmd-close"
    displaypage_command = "cmd-displaypage"
    splashpage_command = "cmd-splashpage"
    def __init__(self, cmd=None, arg=None):
        self.cmd = cmd
        self.arg = arg

    @staticmethod
    def RedrawPage():
        return PageManagerCommand(PageManagerCommand.redraw_command)

    @staticmethod
    def ClosePage():
        return PageManagerCommand(PageManagerCommand.close_command)

    @staticmethod
    def DisplayPage(page):
        return PageManagerCommand(PageManagerCommand.displaypage_command, page)

    @staticmethod
    def SplashPage(page):
        return PageManagerCommand(PageManagerCommand.splashpage_command, page)