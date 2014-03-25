Deform Autoneed README
======================

A simple package to turn any `deform <http://docs.pylonsproject.org/projects/deform>`_
requirements into `Fanstatic <http::/fanstatic.org>`_ resources and serve them.

Some ideas were taken from `js.deform <https://pypi.python.org/pypi/js.deform>`_,
but this package is in many ways its absolute opposite: It only serves whatever content
deform ships with. Hence it should be compatible with any version of deform.

.. note::

    Note: This package patches deforms render function the same way as js.deform does.
    If you don't want that, you can include the rendering yourself.

.. image:: https://travis-ci.org/robinharms/deform_autoneed.svg?branch=master
    :target: https://travis-ci.org/robinharms/deform_autoneed

Tested with the following deform/Python versions:
 - Python 2.7, 3.2, 3.3
 - deform 0.9.5 - Python 2.7
 - deform 0.9.9 - Python 2.7, 3.2, 3.3
 - deform 2.0a.2 - Python 2.7, 3.2, 3.3

It should be compatible with most fanstatic versions,
including current stable 0.16 and future 1.0x.

This package should also work with future versions of deform that are somewhat API-stable.
Should be framework agnostic and compatible with anything that Fanstatic works on. (Any WSGI)


Simple usage
------------

During startup procedure of your app, simply run:

.. code-block:: python

    from deform_autoneed import includeme
    includeme()

Or if you use the Pyramid framework:

.. code-block:: python

    config.include('deform_autoneed')

This will populate the local registry with any resources that deform widgets might need,
and patch deforms render function so they're included automatically.

And that's it!


Using registered resources in other pages
-----------------------------------------

deform prior to 2 depends on jquery, while deform 2 depends on jquery and bootstrap.
If you want any of these base packages in any other view that isn't a form, simply:

.. code-block:: python

    from deform_autoneed import need_lib
    
    need_lib('basic')

Basic means any base requirements of deform itself. You may also call other deform dependencies here.
Essentially, you can use any key from deforms default resource registry in: ``deform.widget.default_resources``.


Replacing a resource requirement
--------------------------------

If you wish to replace a resource with something else, ``ResourceRegistry``
has a method for that. It will have an effect on everything that might
depend on that resource.

Example:

deforms form.css is a registered requirement. We'll replace it with out own css,
where ``our_css`` is a fanstatic resource object.

resource_registry.replace_resource('deform:static/css/form.css', our_css)

Note that ``replace_resource`` accepts either fanstatic.Resource``-objects
or paths with package name, like 'deform:static/css/form.css' as arguments.


Registering a custom widgets resources
--------------------------------------

If you're using any widgets/forms in deform that require non-standard plugins,
you can register them within this package to include them.

First, create a Fanstatic library for your resources and an entry point in your setup.py.
(See the Fanstatic docs for this)

.. code-block:: python

    from fanstatic import Library
    
    my_lib = Library('my_lib', 'my/static')

Add your library to autoneed's registry:

.. code-block:: python

    from deform_autoneed import resource_registry
    
    resource_registry.libraries['my_package_name'] = my_lib

If you have structured your requirements the same way as in ``deform.widget.default_resources``,
and your directory for static resources is called ``static``,
you can call the method populate from resources to automatically create your package.

.. code-block:: python

    resource_registry.populate_from_resources(your_resources)

If not, you can simply add the requirements using the method ``create_requirement_for``.

.. code-block:: python

    resource_registry.create_requirement_for('my_special_widget',
                                             ['my_package_name:my/static/css/cute.css', 'my_package_name:my/static/js/annoying.js'],
                                             )

In other words, this example had the directory layout, where the static directory
is the base of your fanstatic library.

* my_package_name/

  * my/

    * static/

      * css/
      * js/

And the custom widget will require something called 'my_special_widget'.
(See the deform docs on custom widgets)

After this, your dependencies will be included automatically whenever deform needs them.


Bugs, contact etc...
--------------------

* Source/bug tracker: `GitHub <https://github.com/robinharms/deform_autoneed>`_
* Initial author and maintainer: Robin Harms Oredsson `<robin@betahaus.net>`_
* License: GPLv3 or later

