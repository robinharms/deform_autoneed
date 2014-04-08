import logging
import os
import re

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
            
            {'jquery.form': [<Resource 'deform:static/scripts/jquery-1.4.2.min.js'>, <Resource 'deform:static/scripts/jquery.form.js'>]

        libraries
            A dict of fanstatic libraries and their names. By default 'deform' is registered,
            and any package specifying a path that starts with 'deform:' will use this library.
            The convention is that the key for each library must be the same as the package name.
            A resource path like ``deform:some/resouce.js`` will use the library located in self.libraries['deform'].
    """
    requirements = {}
    libraries = {}
    
    def __init__(self, requirements = None, libraries = None, add_basics = True):
        self.requirements = requirements and requirements or {}
        self.libraries = {'deform': deform_autoneed_lib}
        if libraries:
            assert isinstance(libraries, dict)
            self.libraries.update(libraries)
        if add_basics:
            self.add_deform_basics()

    def create_requirement_for(self, requirement_name, resource_paths, requirement_depends = ('basic',)):
        """ Updates path_resource_registry and requirement_registry with information needed to auto_need resources.

            requirement_name
                The first key from deform.widget.default_resources. (like 'jquery'). Sometimes referred to as library.
    
            resource_paths
                Any other arguments should be paths to resources this requirement wants to use.
                They're different depending on version:
                Deform 1: 'scripts/jquery-1.7.2.min.js'
                Deform 2: 'deform:static/scripts/jquery-1.7.2.min.js'
                
                Any relative paths without package specification (the text before the ':') will be considered
                as deform resources.

            requirement_depends
                A list of other requirements that the added resources will depend on.
                It will iterate on all the libraries in these and add them as a dependency.
        """
        requirement = self.requirements.setdefault(requirement_name, [])
        if isinstance(resource_paths, str):
            resource_paths = (resource_paths,)
        previous = None #To inject linear dependencies
        for resource_path in resource_paths:
            #Deform2 prepends path with package name. Deform 1 doesn't.
            path_items = resource_path.split(':')
            if len(path_items) == 2:
                logger.debug("Got resource path '%s' - assuming Deform >= 2" % resource_path)
                #Assume deform 2
                lib_name = path_items[0]
                if lib_name not in self.libraries:
                    raise KeyError("You tried to create requirements for the resource path '%s' which specifies a package that isn't known. "
                                   "Adjust the variable 'library_registry' and add it." % resource_path)
                library = self.libraries[lib_name]
            else:
                logger.debug("Got resource path '%s' - assuming Deform < 2" % resource_path)
                library = self.libraries['deform']
                resource_path = "deform:static/%s" % resource_path            
            depends_on = []
            for depend in requirement_depends:
                depends_on.extend(self.requirements[depend])
            if previous and previous not in depends_on:
                depends_on.append(previous)
            resource = self.create_resource(resource_path, library = library, depends = depends_on)
            if resource not in requirement:
                requirement.append(resource)
            previous = resource

    def create_resource(self, resource_path, library = None, depends = ()):
        """ Create a ``fanstatic.Resource`` object from a path. Returns created object
            or an already existing resource if one already existed.
            
            resource_path
                Specified with package or as an absolute path.

            library
                A ``fanstatic.Library`` you wish to add the resource to.
                It will also be added to the attribute libraries if it doesn't
                already exist. If it alredy exist, it's an optional argument

            depends
                Passed to Resource as dependency. Must be dependable objects
                like ``fanstatic.Resource``.
            
        """
        lib_name, path = resource_path.split(':')
        if lib_name not in self.libraries:
            assert isinstance(library, Library)
            self.libraries[lib_name] = library
        else:
            if library is not None:
                assert library == self.libraries[lib_name]
            else:
                library = self.libraries[lib_name]
        abs_path = pkg_resources.resource_filename(lib_name, path)
        rel_path = abs_path.replace("%s/" % library.path, '')
        if rel_path not in library.known_resources:
            logger.debug("Adding '%s' to lib %s" % (abs_path, library))
            resource = Resource(library, rel_path, depends = depends)
            return resource
        else:
            logger.debug("Resource '%s' already known to lib %s - skipping." % (abs_path, library))
            return library.known_resources[rel_path]
            #fixme: return already existing resource

    def add_deform_basics(self):
        """ Add the basic deform resources, usually needed on all pages.
            Hopefully more intelligent in the future, but right now we
            need to guess the included deform packages in deform2.
        """
        logger.debug("Adding deform basic needs.")
        deform_version = pkg_resources.get_distribution('deform').version
        paths = []
        if deform_version.startswith('0'):
            #Default resources are marked as 'deform' in deform <2
            from deform.widget import default_resources
            for res_type in ('js', 'css'):
                res = default_resources['deform'][None][res_type]
                if isinstance(res, str):
                    paths.append(res)
                else:
                    paths.extend(res)
        else:
            #Deform 2-style has package info as well. We use it as a fanstatic library name too
            #Guess jquery name
            scripts_dir = pkg_resources.resource_filename('deform', 'static/scripts')
            jquery_fname = None
            for fname in os.listdir(scripts_dir):
                if re.match('^jquery\-[0-9]{1,2}(.*)\.min\.js$', fname):
                    jquery_fname = fname
                    break
            if not jquery_fname: #pragma : no coverage
                raise IOError("Can't fint any jquery file within deform.")
            paths.extend(['deform:static/css/form.css',
                          'deform:static/css/bootstrap.min.css',])
            #Pre-register bootstrap and dependency on jquery
            jquery = Resource(deform_autoneed_lib, "scripts/%s" % jquery_fname)
            requirement = self.requirements.setdefault('basic', [])
            requirement.append(jquery)
            bootstrap_js = Resource(deform_autoneed_lib, 'scripts/bootstrap.min.js', depends = (jquery,))
            requirement.append(bootstrap_js)
        self.create_requirement_for('basic', paths, requirement_depends=())

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

    def resource_package_path(self, resource):
        """ Find the resources package path, similar to:
            ``package:some/path/to/resource.css``
            The library must exist in self.libraries since the name of the library
            will be used as package name. (They must always be the same)
            
            resource
                Must be an instance of ``fanstatic.Resource``
        """
        assert isinstance(resource, Resource)
        library = None
        for (name, lib) in self.libraries.items():
            if resource.library == lib:
                library = lib
                break
        if library is None:
            raise KeyError("Couldn't find any matching library for this resource in %s" % self.libraries)
        abs_path = self._resource_fullpath(resource)
        rel_path = abs_path.replace("%s/" % library.path, "%s/" % library.rootpath)
        return "%s:%s" % (name, rel_path)

    def _resource_fullpath(self, resource):
        """ Fetch full path for resource. This already exists in later versions
            of fanstatic, but it's here for compat reasons.
        """
        return os.path.normpath(os.path.join(resource.library.path, resource.relpath))

    def find_resource(self, resource_path):
        """ Find the first instance of a registered resource matching this resource_path.
        
            resource_path
                Can be either a repative path with package name like: ``deform:static/scripts/deform.js``
                or a full path.
        """
        assert isinstance(resource_path, str)
        if ':' in resource_path:
            #Assume package
            resource_path = pkg_resources.resource_filename(*resource_path.split(':'))
        resources = set()
        [resources.update(x) for x in self.requirements.values()]
        for resource in resources:
            if resource_path == self._resource_fullpath(resource):
                return resource

    def remove_resource(self, resource, dependencies = True):
        """ A method to remove a resource from the requirements and from the library it's registered in.
        """
        if isinstance(resource, str):
            resource = self.find_resource(resource)
        assert isinstance(resource, Resource)
        for resources in self.requirements.values():
            if resource in resources:
                resources.remove(resource)
            if dependencies:
                for res in resources:
                    if resource in res.depends:
                        res.depends.remove(resource)
                    if resource in res.resources:
                        res.resources.remove(resource)
        del resource.library.known_resources[resource.relpath]

    def replace_resource(self, old, new, dependencies = True):
        """ Replace a resource with a new one.
            You can either specify a resource as a package path, IE:
            ``somepackage:path/to/file.js``
            or as a ``fanstatic.Resource instance.``
            
            The resource will not be removed from its library, only changed
            
            dependencies
                Also handle dependencies of all resources. A replaced resource
                will also replace dependencies of other resources.
                (For instance, if you replace jquery version, anything depending
                on jquery will depend on your new resource instead)
        """
        if isinstance(old, str):
            old = self.find_resource(old)
        assert isinstance(old, Resource)
        if isinstance(new, str):
            new = self.create_resource(new)
        assert isinstance(new, Resource)
        for resources in self.requirements.values():
            if old in resources:
                pos = resources.index(old)
                resources.insert(pos, new)
            if dependencies:
                for res in resources:
                    if old in res.depends:
                        res.depends.add(new)
                    if old in res.resources:
                        res.resources.add(new)
        self.remove_resource(old, dependencies = dependencies)

resource_registry = ResourceRegistry()


def auto_need(form, reg = None):
    """ Check libraries required by the current widgets.
        Each librarys requirements is stored in the requirements_registry.
    """
    if reg is None: #pragma : no coverage
        reg = resource_registry
    need_lib('basic', reg = reg)
    requirements = form.get_widget_requirements()
    for library, version in requirements:
        for resource in reg.requirements.get(library, ()):
            logger.debug('Including %s via auto_need' % resource)
            resource.need()

def need_lib(lib_name, reg = None):
    """ Call this to include for instance deforms basic components
        or something you may have registered yourself.
        If you're using twitter bootstrap from the deform package,
        just call need_lib('basic') to include it.
    """
    if reg is None: #pragma : no coverage
        reg = resource_registry
    [resource.need() for resource in reg.requirements[lib_name]]

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
