rem SZ ICONS
C:\Panda3D-1.11.0-x64_OFF\bin\egg-texture-cards -o ttrm_m_gui_mvmk_brwsrIcns.egg ../export/*.png

egg-palettize.exe -tn ttrm_t_%%g_palette_%%p_%%i -all -egg -redo -noabs -nodb -af textures.txa -dm output/%%g -d output/ .\*.egg
cd output/
for %%f in (*.egg) do egg2bam -o "%%~nf.bam" %%f
pause