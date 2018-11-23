import logging


class Logger(object):
    def __init__(self, file_name):
        self.file = file_name
        # create logger
        self.logger = logging.getLogger()

        # set default log level
        # self.logger.setLevel(logging.DEBUG)

        # create console_handler and file_handler
        self.console_handler = logging.StreamHandler()
        self.file_handler = logging.FileHandler(self.file, 'w')

        # set log level
        self.console_handler.setLevel(logging.INFO)
        self.file_handler.setLevel(logging.WARNING)

        # create file formatter
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d  - %(message)s')
        self.console_formatter = logging.Formatter('%(levelname)s - %(message)s')

        # add formatter to handler
        self.console_handler.setFormatter(self.console_formatter)
        self.file_handler.setFormatter(self.file_formatter)

        # add handlers to logger
        self.logger.addHandler(self.console_handler)
        self.logger.addHandler(self.file_handler)

    def info(self, log_message, *args, **kwargs):
        self.logger.info(log_message)

    def warning(self, log_message, *args, **kwargs):
        self.logger.warning(log_message)


class Test(Logger()):
    def __init__(self):
        pass

    def test(self, msg):
        Logger.warning(msg)


def main():
    log_name = 'http_download.log'

    l = Logger(log_name)

    def test():
        l.info('hello')
        l.warning('warning')

    test()

    t = Test()
    t.test("xxx")


if __name__ == "__main__":
    main()