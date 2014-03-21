import logging

from fanstatic import (Resource,
                       Library)
import pkg_resources


logger = logging.getLogger(__name__)

deform_static = pkg_resources.resource_filename("deform", "static")
deform_autoneed_lib = Library("deform_autoneed_lib", deform_static)


class ResourceRegistry(object):
    """ Contains and keeps track of resources in a way that is similar to Deforms
        get_widget_requirements method on forms and widgets.
        
        requirements
            A dict with lists as value. Mimics the behaviour of the first level of
            deform.widget.default_resources, but with stripped version information and resource type.
            (Since it isn't relevant for fanstatic)
            
            A typical entry for deform 2 would be:
            
            {'jquery.form': ['deform:static/scripts/jquery-1.4.2.min.js', 'deform:static/scripts/jquery.form.js']
        
        paths
            Mapping path names to actual deform resources. Example:
            {'some_file_name.js': <Resource xxx>, 'deform:static/some/path.js': <Resource xxx>}

        libraries
            A dict of fanstatic libraries and their names. By default 'deform' is registered,
            and any package specifying a path that starts with 'deform:' will use this library.
            If you want to add your own, just modify this dict.
    """
    requirements = {}
    paths = {}
    libraries = {}
    
    def __init__(self, requirements = None, paths = None, libraries = None, add_basics = True):
        self.requirements = requirements and requirements or {}
        self.paths = paths and paths or {}
        self.libraries = libraries and libraries or {'deform': deform_autoneed_lib}
        if add_basics:
            self.add_deform_basics()

    def create_requirement_for(self, requirement_name, resource_paths, remove_leading = 'static/', depends = ('basic',)):
        """ Updates path_resource_registry and requirement_registry with information needed to auto_need resources.

            requirement_name
                The first key from deform.widget.default_resources. (like 'jquery'). Sometimes referred to as library.
    
            resource_paths
                Any other arguments should be paths to resources this requirement wants to use.
                They're different depending on version:
                Deform 1: 'scripts/jquery-1.7.2.min.js'
                Deform 2: 'deform:static/scripts/jquery-1.7.2.min.js'

            remove_leading
                Remove this part of the path if it exist. Look at the difference between deform 1 and 2 paths,
                hence this is needed. This doesn't effect the resource_paths specifications.
                This is also the place to adjust your own custom widget paths.

            depends
                A list of other requirements that the added resources will depend on.
                It will iterate on all the libraries in these and add them as a dependency.
        """
        requirement = self.requirements.setdefault(requirement_name, [])
        if isinstance(resource_paths, str):
            resource_paths = (resource_paths,)
        for resource_path in resource_paths:
            #Deform2 prepends path with package name. Deform 1 doesn't.
            path_items = resource_path.split(':')
            if len(path_items) == 2:
                #Assume deform 2
                lib_name = path_items[0]
                if lib_name not in self.libraries:
                    raise KeyError("You tried to create requirements for the resource path '%s' which specifies a package that isn't known. "
                                   "Adjust the variable 'library_registry' and add it." % resource_path)
                library = self.libraries[lib_name]
                file_path = path_items[1]
                if remove_leading and file_path.startswith(remove_leading):
                    file_path = file_path[len(remove_leading):]
            else:
                #Assume deform 1
                library = self.libraries['deform']
                file_path = resource_path
            if resource_path not in requirement:
                logger.debug("'%s' now requires '%s'" % (library, resource_path))
                requirement.append(resource_path)
            if resource_path not in self.paths:
                logger.debug("Path mapping added for '%s'" % resource_path)
                depends_on = []
                for depend in depends:
                    depends_on.extend([self.paths[x] for x in self.requirements[depend]])
                self.paths[resource_path] = Resource(library, file_path, depends = depends_on)

    def add_deform_basics(self):
        """ Add the basic deform resources, usually needed on all pages.
            Hopefully more intelligent in the future...
        """
        logger.debug("Adding deform basic needs.")
        deform_version = pkg_resources.get_distribution('deform').version
        paths = []
        if deform_version.startswith('0'):
            #Default resources are marked as 'deform' in deform <2
            from deform.widget import default_resources
            paths.extend(default_resources['deform'][None]['js'])
            paths.extend(default_resources['deform'][None]['css'])
        if deform_version.startswith('2'):
            #requirements
            paths.extend(['deform:static/css/form.css',
                          'deform:static/css/bootstrap.min.css',
                          'deform:static/scripts/bootstrap.min.js',
                          'deform:static/scripts/jquery-2.0.3.min.js',])
            #Pre-register bootstrap and dependency on jquery
            jquery = Resource(deform_autoneed_lib, 'scripts/jquery-2.0.3.min.js')
            self.paths['deform:static/scripts/jquery-2.0.3.min.js'] = jquery
            self.paths['deform:static/scripts/bootstrap.min.js'] = Resource(deform_autoneed_lib, 'scripts/bootstrap.min.js',
                                                                           depends = (jquery,))
        self.create_requirement_for('basic', paths, depends=())

    def populate_from_resources(self, resource_specs = None):
        """ Walk through resources from deform or another package
            and create fanstatic resources.
            If resource_specs is another package, it needs to have the same layout as:
            deform.widget.default_resources
        """
        if resource_specs is None:
            from deform.widget import default_resources
            resource_specs = default_resources
        for (requirement_name, rinfo) in resource_specs.items():
            for resources in rinfo.values():
                for (res_type, resource_paths) in resources.items():
                    self.create_requirement_for(requirement_name, resource_paths)


resource_registry = ResourceRegistry()


def auto_need(form, reg = None):
    """ Check libraries required by the current widgets.
        Each librarys requirements is stored in the requirements_registry.
    """
    if reg is None:
        reg = resource_registry
    need_lib('basic', reg = reg)
    requirements = form.get_widget_requirements()
    for library, version in requirements:
        for path in reg.requirements.get(library, ()):
            logger.debug('Including %s via auto_need' % path)
            reg.paths[path].need()

def need_lib(lib_name, reg = None):
    """ Call this to include for instance deforms basic components
        or something you may have registered yourself.
        If you're using twitter bootstrap from the deform package,
        just call need_lib('basic') to include it.
    """
    if reg is None:
        reg = resource_registry
    [reg.paths[path].need() for path in reg.requirements[lib_name]]

def patch_deform():
    """ Copied from js.deform - this package should do the same thing, even though the auto_need
        functions are different. """
    _marker = object()
    from deform import (Form,
                        ValidationFailure)
    logger.debug("Patching deform methods Form.render and ValidationFailure.render to run auto_need.")

    def form_render(self, appstruct=_marker, **kw):
        if appstruct is not _marker:  # pragma: no cover  (copied from deform)
            kw['appstruct'] = appstruct
        html = super(Form, self).render(**kw)
        auto_need(self)
        return html

    def validationfailure_render(self):
        auto_need(self.field)
        return self.field.widget.serialize(self.field, self.cstruct)

    Form.render = form_render
    ValidationFailure.render = validationfailure_render

def includeme(config = None):
    resource_registry.populate_from_resources()
    patch_deform()
