from enum import Enum


class AppStatusEnum(str, Enum):
    CHECK_DEP = "checking_dep"
    INSTALLING_DEP = "installing_dep"
    BUILDING_IMG = "building_img"
    READY = "ready"
    RUNNING = "running"


class BuildToolEnum(str, Enum):
    DOCKER = "docker"
    DEBOOTSTRAP = "debootstrap"


class ToolStatusEnum(str, Enum):
    NOT_INSTALLED = "Not Installled"
    INSTALLED = "Installed"
