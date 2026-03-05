from dataclasses import dataclass

# TODO 暂定的形态不确定，感觉放这里不好，但是后面再想
@dataclass
class Response:
    status_code: int
    text: str
    headers: dict[str, str]
    url: str