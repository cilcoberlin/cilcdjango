
from cilcdjango.core.util import get_app_setting

import os

UPLOADED_FILES_DIRECTORY = "media_libraries"
ADD_MEDIA_FORM_AUTO_ID = "id_media_%s"
ADD_GROUP_FORM_AUTO_ID = "id_group_%s"

MEDIA_PLAYER_URL = "flash/jwplayer/player.swf"

MEDIA_URL = os.path.join(get_app_setting('SHARED_MEDIA_URL'), 'medialibrary')
