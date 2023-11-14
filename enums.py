from enum import Flag, StrEnum


class Intention(StrEnum):
    """游戏风格"""

    SOCIAL = "social"  # 社交
    COOPERATIVE = "cooperative"  # 合作
    COMPETITIVE = "competitive"  # 竞争
    MADNESS = "madness"  # 疯狂


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

    WILSON = "wilson"
    WILLOW = "willow"
    WENDY = "wendy"
    WOLFGANG = "wolfgang"
    WX78 = "wx78"
    WICKERBOTTOM = "wickerbottom"
    WES = "wes"
    WAXWELL = "waxwell"
    WOODIE = "woodie"
    WATHGRITHR = "wathgrithr"
    WEBBER = "webber"
    WINONA = "winona"
    WORTOX = "wortox"
    WORMWOOD = "wormwood"
    WARLY = "warly"
    WURT = "wurt"
    WALTER = "walter"
    WANDA = "wanda"
    WONKEY = "wonkey"


class Season(StrEnum):
    """游戏季节"""

    AUTUMN = "autumn"
    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"


class VersionType(StrEnum):
    """版本类型"""

    RELEASE = "Release"
    TEST = "Test"
