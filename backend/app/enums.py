from enum import Enum

class AppStatusEnum(str,Enum):
    CHECK_DEP="check_dep"
    INSTALLING_DEP="installing_dep"
    BUILDING_IMG="building_img"
    READY="ready"
    RUNNING="running"

class BuildToolEnum(str,Enum):
    DOCKER="docker"
    DEBOOTSTRAP="normal"