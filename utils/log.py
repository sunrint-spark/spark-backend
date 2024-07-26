import logging

logging.basicConfig(
    format="[%(name)s] (%(asctime)s) %(levelname)s:%(message)s",
    datefmt="%m/%d %I:%M:%S %p",
)


class Logger:
    @staticmethod
    def create(
        name: str, /, level: int, file_name: str | None = None
    ) -> logging.Logger:
        new_logger = logging.getLogger(name)

        new_logger.setLevel(level)

        stream_handler = logging.StreamHandler()
        new_logger.addHandler(stream_handler)

        if not file_name is None:
            file_handler = logging.FileHandler(f"logs/{file_name}.log")
            new_logger.addHandler(file_handler)

        return new_logger

    @staticmethod
    def dev(name: str, /) -> logging.Logger:
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        new_logger.addHandler(stream_handler)
        return new_logger

    @staticmethod
    def prd(name: str, /, file_name: str | None = None) -> logging.Logger:
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        new_logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(f"logs/{file_name or name}.log")
        new_logger.addHandler(file_handler)

        return new_logger

    @staticmethod
    def warn(name: str, /, file_name: str | None = None) -> logging.Logger:
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.WARN)

        stream_handler = logging.StreamHandler()
        new_logger.addHandler(stream_handler)

        if not file_name is None:
            file_handler = logging.FileHandler(f"logs/{file_name}.log")
            new_logger.addHandler(file_handler)

        return new_logger

    @staticmethod
    def error(name: str, /, file_name: str | None = None) -> logging.Logger:
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.ERROR)

        stream_handler = logging.StreamHandler()
        new_logger.addHandler(stream_handler)

        if not file_name is None:
            file_handler = logging.FileHandler(f"logs/{file_name}.log")
            new_logger.addHandler(file_handler)

        return new_logger
