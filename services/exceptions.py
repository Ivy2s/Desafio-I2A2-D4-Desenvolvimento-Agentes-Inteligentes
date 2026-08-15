class DatasetNotFoundError(Exception):
    code = "dataset_not_found"


class UnsupportedFileError(Exception):
    code = "unsupported_file_type"


class InvalidDatasetError(Exception):
    code = "dataset_load_failed"


class UploadTooLargeError(InvalidDatasetError):
    code = "upload_too_large"


class UnsafeZipEntryError(InvalidDatasetError):
    code = "unsafe_zip_entry"


class InvalidZipError(InvalidDatasetError):
    code = "invalid_zip"


class NoCsvFilesFoundError(InvalidDatasetError):
    code = "no_csv_files_found"


class ZipLimitExceededError(InvalidDatasetError):
    code = "zip_limit_exceeded"


class AIUnavailableError(Exception):
    code = "ai_provider_unavailable"


class AgentExecutionError(Exception):
    code = "query_execution_error"


class UnknownToolError(AgentExecutionError):
    code = "unknown_tool"


class ToolExecutionError(AgentExecutionError):
    code = "tool_execution_failed"


class AgentTimeoutError(AgentExecutionError):
    code = "agent_timeout"


class AgentIterationLimitError(AgentExecutionError):
    code = "agent_iteration_limit"
