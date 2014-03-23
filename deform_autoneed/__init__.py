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
            
            {'jquery.form': [<Resource 'deform:static/scripts/jquery-1.4.2.min.js'>, <Resource 'deform:static/scripts/jquery.form.js'>]

        libraries
            A dict of fanstatic libraries and their names. By default 'deform' is registered,
            and any package specifying a path that starts with 'deform:' will use this library.
            If you want to add your own, just modify this dict.
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

    def create_requirement_for(self, requirement_name, resource_paths, depends = ('basic',)):
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
            abs_path = pkg_resources.resource_filename(*resource_path.split(':'))
            rel_path = abs_path.replace("%s/" % deform_autoneed_lib.rootpath, '')
            if rel_path not in deform_autoneed_lib.known_resources:
                logger.debug("Adding '%s' to lib %s" % (abs_path, library))
                depends_on = []
                for depend in depends:
                    depends_on.extend(self.requirements[depend])
                resource = Resource(library, rel_path, depends = depends_on)
                requirement.append(resource)
            else:
                logger.debug("Resource '%s' already known to lib %s - skipping." % (abs_path, library))

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
            import os
            import re
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
