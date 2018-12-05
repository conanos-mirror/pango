from conans import ConanFile, CMake, tools, Meson
from conanos.build import config_scheme
import os


class PangoConan(ConanFile):
    name = "pango"
    version = "1.42.4"
    description = "Internationalized text layout and rendering library"
    url = 'https://github.com/conanos/pango'
    homepage = 'https://www.pango.org/'
    license = "LGPL-v2+"
    patch = ["language-sample-table.patch", "example-shape-dot.patch"]
    exports = ["COPYING"] + patch
    generators = "gcc","visual_studio"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        'fPIC': [True, False]
    }
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def requirements(self):
        self.requires.add("cairo/1.15.12@conanos/stable")
        self.requires.add("fontconfig/2.13.0@conanos/stable")
        self.requires.add("freetype/2.9.1@conanos/stable")    
        self.requires.add("harfbuzz/2.1.3@conanos/stable")
        self.requires.add("glib/2.58.1@conanos/stable")
        self.requires.add("fribidi/1.0.5@conanos/stable")
    
    def build_requirements(self):
        self.build_requires("libffi/3.299999@conanos/stable")
        self.build_requires("libpng/1.6.34@conanos/stable")
        self.build_requires("zlib/1.2.11@conanos/stable")
        self.build_requires("bzip2/1.0.6@conanos/stable")
        self.build_requires("expat/2.2.5@conanos/stable")
        self.build_requires("pixman/0.34.0@conanos/stable")
        if self.settings.os == "Linux":
            self.build_requires("libuuid/1.0.3@conanos/stable")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
    
    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_ = 'https://github.com/GNOME/pango/archive/{version}.tar.gz'.format(version=self.version)
        tools.get(url_)
        if self.settings.os == "Windows":
            for p in self.patch:
                tools.patch(patch_file=p)
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        pkg_config_paths=[ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") 
                           for i in ["fontconfig","freetype","harfbuzz","glib","libffi","fribidi","cairo"] ]
        pkg_config_paths.extend([ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") 
                                  for i in ["libpng","pixman","zlib","bzip2","expat"] ])
        if self.settings.os == "Linux":
            pkg_config_paths.extend([ os.path.join(self.deps_cpp_info[i].rootpath, "lib", "pkgconfig") for i in ["libuuid"] ])
        prefix = os.path.join(self.build_folder, self._build_subfolder, "install")
        binpath=[ os.path.join(self.deps_cpp_info[i].rootpath, "bin") for i in ["glib"] ]
        include = [ os.path.join(self.deps_cpp_info["fontconfig"].rootpath, "include"),
                    os.path.join(self.deps_cpp_info["freetype"].rootpath, "include","freetype2"),
                    os.path.join(self.deps_cpp_info["cairo"].rootpath, "include","cairo")
                  ]
        libpath = [ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["libffi", "libpng", "bzip2"] ]
        meson = Meson(self)
        if self.settings.os == "Linux":
            with tools.environment_append({
                'PATH' : os.pathsep.join(binpath + [os.getenv('PATH')]),
                'C_INCLUDE_PATH' : os.pathsep.join(include),
                'CPLUS_INCLUDE_PATH' : os.pathsep.join(include),
                'LD_LIBRARY_PATH' : os.pathsep.join(libpath),
                }):
                meson.configure(defs={'prefix' : prefix, 'libdir':'lib','gir' : 'false'},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))
        
        if self.settings.os == 'Windows':
            libpath.extend([ os.path.join(self.deps_cpp_info[i].rootpath, "lib") for i in ["zlib"] ])
            with tools.environment_append({
                'PATH' : os.pathsep.join(binpath + [os.getenv('PATH')]),
                "INCLUDE" : os.pathsep.join(include + [os.getenv('INCLUDE')]),
                'LIB'  : os.pathsep.join(libpath + [os.getenv('LIB')]),
                }):
                meson.configure(defs={'prefix' : prefix, 'gir' : 'false'},
                                source_dir=self._source_subfolder, build_dir=self._build_subfolder,
                                pkg_config_paths=pkg_config_paths)
                meson.build()
                self.run('ninja -C {0} install'.format(meson.build_dir))

    def package(self):
        self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._build_subfolder, "install"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

