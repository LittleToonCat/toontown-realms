# This is the PRC configuration file for settings that are
# specific to production instances of Toontown Realms.

# Disable loader entry points because we can't use importlib in pypperoni
loader-support-entry-points false

# Window settings
window-title Toontown Realms

# Notify settings
console-output true
# uncomment below and/or add to it if restricted notify calls are wanted/needed
notify-level info
default-directnotify-level info
notify-level-ToontownUberRepository info
notify-level-ToontownAIRepository info

# Server settings
server-version VERSION_STRING

# Developer settings
want-dev false
schellgames-dev false
exec-chat false
log-private-info false
want-qa-regression false
want-discord-rpc true

# Audio settings
audio-library-name p3openal_audio

# Resources settings
model-cache-models false
model-cache-textures false

# discord rich presence stuff
want-discord-avatars true
