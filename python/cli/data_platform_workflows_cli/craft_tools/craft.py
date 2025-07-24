import enum


class Architecture(str, enum.Enum):
    X64 = "amd64"
    ARM64 = "arm64"
    S390X = "s390x"


class Craft(str, enum.Enum):
    SNAP = "snap"
    ROCK = "rock"
    CHARM = "charm"
