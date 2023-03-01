import logging

logging.basicConfig(level=logging.DEBUG, filename="py_log.log",filemode="w")

class LoggingRest:

    def __init__(self):
        pass

    def get(self, link: str, func,response):
        logging.debug(f"GET (\"{link}\"), func({func}): {response}")

    def post(self, link: str, func, response):
        logging.debug(f"POST (\"{link}\"), func({func}): {response}")

    def put(self, link: str, func, response):
        logging.debug(f"PUT (\"{link}\"), func({func}): {response}")

    def delete(self, link: str, func, response):
        logging.debug(f"DELETE (\"{link}\"), func({func}): {response}")


rest_log = LoggingRest()