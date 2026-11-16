# This is the PRC configuration file for settings that are
# specific to developer instances of Toontown Realms.

# Window settings
window-title Toontown Realms [DEV]

# Notify settings
console-output true
notify-level-Prop debug
notify-level-PropPool debug
notify-level-MiniserverAPI debug
notify-level-dna info
notify-level-RealmsSettings info

# Server settings
server-version ttrealms-dev

# Developer settings
want-dev false
allow-unclean-exit true
schellgames-dev false
exec-chat true
log-private-info true
want-qa-regression true

# Put any usernames here for editing in a group environment;
# don't use 'edittoon' in a group environment if you don't want
# others editing your stuff
level-edit-username edittoon

# The current user's username
local-level-edit-username edittoon

# This can be changed on a dev or QA server to save specs remotely
# if editing in a group environment
large-blob-path .

# Starting tk without using want-tk
# locks everything up
# unless you do this
tk-main-loop #f

want-injector false
want-pstats false

# Audio settings
audio-library-name p3openal_audio

# Resources settings
vfs-mount resources/phase_3 /phase_3
vfs-mount resources/phase_3.5 /phase_3.5
vfs-mount resources/phase_4 /phase_4
vfs-mount resources/phase_5 /phase_5
vfs-mount resources/phase_5.5 /phase_5.5
vfs-mount resources/phase_6 /phase_6
vfs-mount resources/phase_7 /phase_7
vfs-mount resources/phase_8 /phase_8
vfs-mount resources/phase_9 /phase_9
vfs-mount resources/phase_10 /phase_10
vfs-mount resources/phase_11 /phase_11
vfs-mount resources/phase_12 /phase_12
vfs-mount resources/phase_13 /phase_13
vfs-mount resources/phase_14 /phase_14
vfs-mount resources/phase_14.5 /phase_14.5
vfs-mount resources/phase_3/models /models

# DC file
dc-file astron/dclass/ttoff.dc

# discord rich presence stuff
want-discord-avatars #t
want-discord-rpc #t