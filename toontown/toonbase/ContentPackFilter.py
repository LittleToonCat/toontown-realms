from panda3d.core import get_model_path, Filename, LoaderOptions, PNMImage, TexturePool, Texture, VirtualFileSystem
import os


class ContentPackFilter(object):
    # The alpha map keeps track of whether our PNG files have an alpha channel or not.
    alpha_map = {}

    @staticmethod
    def load_img(vfs, model_path, path):
        """
        Tries to load an image from the VFS.
        Returns a PNMImage if the image has been read, but None otherwise.
        """
        filename = Filename(path)

        # Resolve the filename using the VFS
        if not vfs.resolve_filename(filename, model_path):
            # The file could not be found within the VFS.
            return None

        # Open a read stream using the VFS
        stream = vfs.open_read_file(filename, False)

        if stream is None:
            # The file could not be read.
            return None

        # Read the image using the stream!
        img = PNMImage()
        img.read(stream)

        # Close the stream before we return the image.
        vfs.close_read_file(stream)

        if img.is_valid():
            # A valid image has been read!
            return img

    @staticmethod
    def resize_img_to(img, source):
        """
        Resizes an image to the same size of the source image.
        """
        if img.get_size() == source.get_size():
            # The two images are already the same size
            return img

        # Resize image to new dimensions
        resized = PNMImage(source.get_x_size(), source.get_y_size(), img.get_num_channels(), img.get_maxval(),
                           img.get_type())
        resized.gaussian_filter_from(1.0, img)

        # Clear old image data
        img.clear()

        return resized

    @staticmethod
    def load_alpha_mix(vfs, model_path, jpg_path, png_path):
        """
        This method combines a JPG's image data and a PNG's alpha data.
        This is necessary because some content packs do not ship the RGB files.
        Reading only the JPG files in this case would result in a texture without an alpha channel.
        Since we do not ship RGB files anymore, we must extract the alpha channel manually from the PNG file.
        """
        png = None

        if png_path not in ContentPackFilter.alpha_map:
            # Looks like our PNG has not been read before.
            # Does it have an alpha channel?
            png = ContentPackFilter.load_img(vfs, model_path, png_path)
            ContentPackFilter.alpha_map[png_path] = png is not None and png.has_alpha()

            if png is not None and not png.has_alpha():
                # Our PNG has been read, but does not have an alpha channel.
                # We won't need this PNG anymore, so let's clear it from memory.
                png.clear()

        if not ContentPackFilter.alpha_map[png_path]:
            # This PNG does not have an alpha channel, so we can't load a mixed image.
            return None

        if png is None:
            # Load our PNG file!
            png = ContentPackFilter.load_img(vfs, model_path, png_path)

            if png is None:
                # Our PNG could not be read, we can't load a mixed image.
                return None

        # Load our JPG file!
        jpg = ContentPackFilter.load_img(vfs, model_path, jpg_path)

        if jpg is None:
            # Our JPG file could not be read, we can't load a mixed image.
            return None

        # Convert the JPG to an alpha channel image
        jpg.set_num_channels(4)

        # Copy the alpha channel from the PNG to the JPG
        png = ContentPackFilter.resize_img_to(png, jpg)
        jpg.copy_channel(png, png.get_num_channels() - 1, jpg.get_num_channels() - 1)

        # Clear the PNG data, as we don't need it anymore
        png.clear()

        # Create our mixed Texture, containing image data from the JPG and alpha data from the PNG
        tex = Texture(os.path.basename(png_path))
        tex.load(jpg)

        # Clear the JPG data, as it has already been loaded into a texture.
        jpg.clear()

        return tex

    @staticmethod
    def pre_load(orig_filename, orig_alpha_filename,
                 primary_file_num_channels, alpha_file_channel,
                 read_mipmaps, options):
        if orig_filename.get_extension().lower() != 'png':
            # Not a PNG, we don't have to look for older JPG textures
            return None

        path = orig_filename.get_fullpath_wo_extension()
        vfs = VirtualFileSystem.get_global_ptr()
        model_path = get_model_path().get_value()
        reg_path = None

        # Older format textures can be both JPG or RGB, let's find the texture.
        for ext in ['.jpg', '.rgb']:
            ext_path = path + ext

            if vfs.resolve_filename(ext_path, model_path):
                # We've found the texture from the content pack!
                reg_path = ext_path
                break

        if reg_path is None:
            # This texture could not be found in any content packs.
            # Leave it to the game engine to load the PNG texture.
            return None

        rgb_path = path + '_a.rgb'
        tex = None

        # Important options:
        # We remove LF_report_errors, as we don't want the console to be spammed if we can't find a texture
        # We add TF_no_filters, as we don't want to get caught in a filter deadlock
        load_options = LoaderOptions(
                options.get_flags() & (~LoaderOptions.LF_report_errors),
                options.get_texture_flags() | (LoaderOptions.TF_no_filters)
        )

        if vfs.resolve_filename(rgb_path, model_path):
            # We've got an RGB file too, let's load it as well.
            tex = TexturePool.load_texture(
                    reg_path, rgb_path, primary_file_num_channels,
                    alpha_file_channel, read_mipmaps, load_options
            )

        if tex is None:
            # We couldn't load the RGB file.
            # Let's see if we can extract an alpha image somehow...
            tex = ContentPackFilter.load_alpha_mix(vfs, model_path, reg_path, orig_filename.get_fullpath())

        if tex is None:
            # Let's just load the JPG itself.
            tex = TexturePool.load_texture(
                    reg_path, primary_file_num_channels,
                    read_mipmaps, load_options
            )

        return tex
