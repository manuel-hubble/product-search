from enum import Enum


class Part(Enum):
    APPLICATION = 0
    HARDWARE = 1
    OPERATING_SYSTEM = 2

    def __str__(self):
        return self.name.lower()

    def to_code(self) -> str:
        cpe_codes: list[str] = ["a", "h", "o"]
        return cpe_codes[self.value]
