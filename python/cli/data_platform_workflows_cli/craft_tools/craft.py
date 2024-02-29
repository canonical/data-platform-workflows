import enum


class Architecture(str, enum.Enum):
    X64 = "amd64"
    ARM64 = "arm64"


class Craft(str, enum.Enum):
    SNAP = "snap"
    ROCK = "rock"
    CHARM = "charm"
