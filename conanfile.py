from conans import ConanFile, CMake, tools, Meson
import os


class PangoConan(ConanFile):
    name = "pango"
    version = "1.40.14"
    description = "Internationalized text layout and rendering library"
    url = 'https://github.com/conanos/pango'
    homepage = 'https://www.pango.org/'
    license = "LGPL-v2+"
    exports = ["COPYING"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = ('cairo/1.14.12@conanos/dev','fontconfig/2.12.6@conanos/dev','freetype/2.9.0@conanos/dev',
    'harfbuzz/1.7.5@conanos/dev','libffi/3.3-rc0@conanos/dev','pixman/0.34.0@conanos/dev',
    'libpng/1.6.34@conanos/dev','gobject-introspection/1.58.0@conanos/dev')

    source_subfolder = "source_subfolder"
    patches = ['PKGCONFIG_CAIRO_REQUIRES-convert-value-to-string.patch']

    def source(self):
        url_ = 'https://github.com/GNOME/pango/archive/{version}.tar.gz'.format(version=self.version)
        patch_url_ = 'https://raw.githubusercontent.com/conanos/pango/master/{patch}'
        tools.get(url_)
        for patch in self.patches:
            tools.download(patch_url_.format(patch=patch), patch)
            tools.patch(patch_file=patch)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            with tools.environment_append({
                'PATH':'%s/bin:%s'%(self.deps_cpp_info["gobject-introspection"].rootpath, os.getenv("PATH")),
                'LD_LIBRARY_PATH':'%s/lib'%(self.deps_cpp_info["libffi"].rootpath),
                }):

                meson = Meson(self)
                meson.configure(
                    defs={'prefix':'%s/builddir/install'%(os.getcwd()), 'libdir':'lib','enable_docs':'false',},
                    source_dir = '%s'%(os.getcwd()),
                    build_dir= '%s/builddir'%(os.getcwd()),
                    pkg_config_paths = [
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["cairo"].rootpath),
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["fontconfig"].rootpath),
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["freetype"].rootpath),
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["harfbuzz"].rootpath),
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["pixman"].rootpath),
                        '%s/lib/pkgconfig'%(self.deps_cpp_info["libpng"].rootpath),
                        ])
                meson.build(args=['-j2'])
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir/install"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

