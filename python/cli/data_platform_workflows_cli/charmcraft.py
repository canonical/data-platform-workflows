import enum


class Architecture(str, enum.Enum):
    X64 = "amd64"
    ARM64 = "arm64"
