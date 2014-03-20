from fanstatic import (Resource,
                       Library)
from pkg_resources import resource_filename


deform_static = resource_filename("deform", "static")
deform_autoneed_lib = Library("deform_autoneed_lib", deform_static)


resource_registry = {}


def auto_need(form):
    pass

def auto_create():
    pass

def populate_resource_registry():
    pass

def patch_deform():
    pass

def includeme(config):
    populate_resource_registry()
    patch_deform()
