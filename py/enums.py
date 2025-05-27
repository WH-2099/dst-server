from enum import Flag, StrEnum, auto


class OnewordType(StrEnum):
    """一言类型"""

    动画 = "a"
    漫画 = "b"
    游戏 = "c"
    文学 = "d"
    原创 = "e"
    来自网络 = "f"
    其他 = "g"
    影视 = "h"
    诗词 = "i"
    网易云 = "j"
    哲学 = "k"
    抖机灵 = "l"


class Platform(Flag):
    """游戏平台"""

    Steam = 1
    PSN = 2
    Rail = 4
    XBone = 16
    Switch = 32


class Region(StrEnum):
    """游戏区域
    虽然有接口，但是这个很少变动，手动维护
    """

    US_EAST = "us-east-1"
    EU_CENTRAL = "eu-central-1"
    AP_SOUTHEAST = "ap-southeast-1"
    AP_EAST = "ap-east-1"


class Role(StrEnum):
    """游戏角色"""

    WILSON = auto()
    WILLOW = auto()
    WENDY = auto()
    WOLFGANG = auto()
    WX78 = auto()
    WICKERBOTTOM = auto()
    WES = auto()
    WAXWELL = auto()
    WOODIE = auto()
    WATHGRITHR = auto()
    WEBBER = auto()
    WINONA = auto()
    WORTOX = auto()
    WORMWOOD = auto()
    WARLY = auto()
    WURT = auto()
    WALTER = auto()
    WANDA = auto()
    WONKEY = auto()
    UNKNOWN = ""


class Intent(StrEnum):
    """游戏风格"""

    ENDLESS = auto()
    LIGHTSOUT = auto()
    RELAXED = auto()
    SURVIVAL = auto()
    WILDERNESS = auto()
    COOPERATIVE = auto()
    OCEANFISHING = auto()


class Season(StrEnum):
    """游戏季节"""

    AUTUMN = auto()
    """秋季"""

    WINTER = auto()
    """冬季"""

    SPRING = auto()
    """春季"""

    SUMMER = auto()
    """夏季"""

    MILD = auto()
    """温和季"""

    HURRICANE = auto()
    """飓风季"""

    MONSOON = auto()
    """雨季"""

    DRY = auto()
    """旱季"""

    TEMPERATE = auto()
    """平和季"""

    HUMID = auto()
    """潮湿季"""

    LUSH = auto()
    """繁茂季"""

    APORKALYPSE = auto()

    WET = auto()

    GREEN = auto()


class VersionType(StrEnum):
    """版本类型"""

    RELEASE = "Release"
    TEST = "Test"
