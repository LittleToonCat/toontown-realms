# This is the PRC configuration file for settings that are
# used by both developer & production instances of Toontown Realms.

# Window settings (Start at center of the screen.)
win-origin -2 -2

# Notify settings
notify-level-collide warning
notify-level-chan warning
notify-level-gobj warning
notify-level-loader warning
notify-integrate false
notify-timestamp true
notify-level-MiniserverAPI warning
notify-level-ClockDelta warning
default-directnotify-level info

# Server settings
ttoff-specific-login true

# position updates
# 0.04 is 25 times a second. 
# We can get away with this on TTRealms due to servers having
# small amounts of players
smooth-lag 0.06
smooth-prediction-lag 0.08
pos-update-rate 0.04
pet-pos-broadcast-period 0.04
smooth-min-suggest-resync 5

# Resources settings
model-path /
default-model-extension .bam

# Add filters path as a readable source
vfs-mount filters /filters

# Display settings
depth-bits 24
aux-display p3tinydisplay
textures-power-2 none
preload-textures false
preload-simple-textures true
allow-incomplete-render true
gl-depth-zero-to-one true
text-use-harfbuzz false

# GUI settings
direct-wtext false
on-screen-debug-font phase_3/fonts/ttoff_f_debug.otf

# Chat settings
parent-password-set true
allow-secret-chat true
force-avatar-understandable true
force-player-understandable true

# Toon News settings
want-news-page false
want-news-tab false

# Gameplay settings
want-gardening true
want-cogdominiums true
want-emblems true
want-special-zone-portal true

# Misc. settings
respect-prev-transform true
language english
vfs-case-sensitive false
inactivity-timeout 180
merge-lod-bundles false
early-event-sphere true
server-data-folder backups/
isclient-check false
active-holidays 64, 65, 66
max-frame-rate-interval 0.2
hardware-animated-vertices true
egg-object-type-smooth-floors   <Collide> { Polyset descend } <Scalar> from-collide-mask { 0x000fffff } <Scalar> into-collide-mask { 0x00000002 }

# Screenshot prefixes

# First one is the currently used one
# for new screenshots
screenshot-prefix ttrealms

# All others will be read as valid
# by the page in the book
screenshot-prefix screenshot
screenshot-prefix ttrealms-screenshot