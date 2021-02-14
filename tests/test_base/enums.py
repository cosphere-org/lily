
from enum import Enum, unique


@unique
class AccountType(Enum):

    ANONYMOUS = 'ANONYMOUS'

    FREE = 'FREE'


@unique
class MediaItemUsageType(Enum):

    MEDIAITEM = 'MEDIAITEM'

    AVATAR = 'AVATAR'


@unique
class MediaItemType(Enum):

    CANVAS = 'CANVAS'

    IMAGE = 'IMAGE'
