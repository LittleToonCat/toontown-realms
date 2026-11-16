"""
Filter Manager

drewcification 020421 - mostly based off of my ShaderRegistry from OTT
"""
import json

from direct.directnotify import DirectNotifyGlobal
from direct.filter import FilterManager as DirectFilterManager
from direct.stdpy.file import exists, listdir, open
from panda3d.core import Shader, NodePath, Texture, FrameBufferProperties


class Filter:
    """
    Filter class
    Nicely stores all data for each filter
    """

    def __init__(self, displayname, identifier, mwidentifiers, fragment, vertex,
                 shadertype):
        """
        :param displayname: Display name of the filter - shows in game (e.g. in MW return message)
        :param identifier: Unique identifier
        :param mwidentifiers: List of identifiers that can be used in the ~filter mw
        :param fragment: File path to the Fragment shader
        :param vertex: File path to the Vertex shader
        :param shadertype: Type of filter (render or postprocess; unused currently)
        """
        self.displayName = displayname
        self.identifier = identifier
        self.mwIdentifiers = mwidentifiers
        self.fragment = fragment
        self.vertex = vertex
        self.type = shadertype

        # Incase we already loaded it, we can store that so we don't reload
        self.loadedShader = None

    def load(self):
        """
        Loads and returns the Shader Object
        :return: Shader Object
        """
        if not self.loadedShader:
            self.loadedShader = Shader.load(Shader.SL_GLSL, fragment = self.fragment, vertex = self.vertex)

        return self.loadedShader

    def activate(self, affectA2d = False, lock = False):
        """
        Activates the filter
        :param affectA2d: Allow the filter to affect the UI (render shaders only)
        :param lock: Locks the filter manager preventing use of the ~filter command
        """
        # Deactivate any loaded filter
        if FilterManager.activeFilter:
            FilterManager.activeFilter.deactivate()

        FilterManager.activeFilter = self

        # Apply a lock if wanted
        FilterManager.filterLocked = lock

        # Load & apply the shader
        shader = self.load()

        if self.type == 'postprocess':
            FilterManager.configureFilterManager()
            FilterManager.filterQuad.setShader(shader)
            FilterManager.updateInputs()
        else:
            render.setShader(shader)
            if affectA2d:
                aspect2d.setShader(shader)

    def deactivate(self):
        """
        Deactivates and cleans up the active filter
        """
        FilterManager.filterLocked = False

        if self.type == 'postprocess':
            FilterManager.cleanupFilterManager()
        else:
            aspect2d.clearShader()
            render.clearShader()

        FilterManager.activeFilter = None


class FilterManager:
    """
    FilterManager class
    Static class used to load and manage visual filters

    Usage:
    == Activating Filters ==
    filter: Filter = FilterManager.findFilter('ttrealms:water')
    filter.activate() (This can be passed with a lock = True to prevent users changing via commands. Useful for using
                       filters in actual gameplay)

    == Deactivating Filters ==
    FilterManager.activeFilter.deactivate()
    """

    # Dict of all loaded filters Identified by ID
    filters = {}

    notify = DirectNotifyGlobal.directNotify.newCategory('FilterManager')

    filterManager = None
    filterQuad = None

    filterTextures = {'color': Texture(), 'depth': Texture()}

    activeFilter = None

    # Not functional yet, will be used to disable users changing filters
    # e.g. if a filter is used for something else like underwater
    filterLocked = False

    @staticmethod
    def configureFilterManager():
        """
        Configure the direct filter manager
        """
        fm = FilterManager

        if not FilterManager.filterManager:
            fm.filterManager = DirectFilterManager.FilterManager(base.win, base.cam)
            fm.filterQuad = fm.filterManager.renderSceneInto(
                    colortex = fm.filterTextures['color'],
                    depthtex = fm.filterTextures['depth'],
                    )
            fm.filterQuad.setShaderInput('color_texture', fm.filterTextures['color'])
            fm.filterQuad.setShaderInput('depth_texture', fm.filterTextures['depth'])

    @staticmethod
    def cleanupFilterManager():
        """
        Cleans up the direct filter manager
        """
        if FilterManager.filterManager:
            FilterManager.filterManager.cleanup()
            FilterManager.filterQuad.removeNode()

        FilterManager.filterManager = None
        FilterManager.filterQuad = None

    @staticmethod
    def updateInputs():
        """
        Update shader inputs like resolution and other info
        """
        if FilterManager.filterQuad:
            FilterManager.filterQuad.setShaderInput('resolution', base.getSize())
        render.setShaderInput('resolution', base.getSize())
        aspect2d.setShaderInput('resolution', base.getSize())

    @staticmethod
    def searchForFilters():
        """
        Searches the phase_3/filters and the ROOTDIR/filters folders for .json files, then parses them
        """
        # Remove any currently loaded filters
        for _filter in FilterManager.filters:
            del _filter
        FilterManager.filters = {}

        filterFiles = []
        # The listdir() func from direct.stdpy works nicely with VFS
        # Search the phase_3/filters folder
        if __debug__:
            # This works differently on DEV
            for file in listdir("resources/phase_3/filters/"):
                if file.endswith('.json'):
                    filterFiles.append(f'resources/phase_3/filters/{file}')
        else:
            for file in listdir("/phase_3/filters/"):
                if file.endswith('.json'):
                    filterFiles.append(f'/phase_3/filters/{file}')

        # Search the rootdir/filters folder
        if exists('filters/'):
            for file in listdir("filters/"):
                if file.endswith('.json'):
                    filterFiles.append(f'filters/{file}')

        for file in filterFiles:
            with open(file, 'r') as filterFile:
                jsonData = json.load(filterFile)
                FilterManager.notify.debug(f"Read JSON Data from {file}: {jsonData}")
                _filter = Filter(
                        displayname = jsonData['display_name'],
                        identifier = jsonData['identifier'],
                        mwidentifiers = jsonData['mw_identifiers'],
                        fragment = jsonData['fragment'],
                        vertex = jsonData['vertex'],
                        shadertype = jsonData['type']
                        )
                # Make sure this unique identifier hasnt been registered already
                if jsonData['identifier'] in FilterManager.filters:
                    # If it has, don't register it
                    FilterManager.notify.warning(f"Found duplicate identifier ({jsonData['identifier']})! Not "
                                                 f"registering!")
                else:
                    FilterManager.notify.info(f"Registering filter {jsonData['identifier']}")
                    FilterManager.filters[jsonData['identifier']] = _filter

    @staticmethod
    def findFilter(identifier):
        """
        :param identifier: MW Identifier to search
        :return: Filter object (if any)
        """

        # If the user inputs the unique identifier (e.g. ttrealms:desaturate)
        if identifier in FilterManager.filters:
            return FilterManager.filters[identifier]

        # if the user inputs a mw identifier (e.g. bandw)
        for _filter in FilterManager.filters.values():
            if identifier in _filter.mwIdentifiers:
                return _filter
        return None
