class Logger:
    def __init__(self, filepath):
        self.filepath = filepath

    def write(self, msg):
        with open(self.filepath, "a") as logfile:
           logfile.write("{}\n".format(msg))
