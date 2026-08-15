class DatasetNotFoundError(Exception):
    pass


class UnsupportedFileError(Exception):
    pass


class InvalidDatasetError(Exception):
    pass


class AIUnavailableError(Exception):
    pass


class AgentExecutionError(Exception):
    pass


class AgentIterationLimitError(AgentExecutionError):
    pass
