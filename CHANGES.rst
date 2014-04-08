Changelog
=========

0.2.2b (2014-04-08)
-------------------

- Resource dependencies consider the order deform list them.
  A widget requirement with several listed resources will have them depend on each other in order.

0.2.1b (2014-04-08)
-------------------

- NOTE: ``remove_resources`` changed to ``remove_resource`` - it only accepts
  one resource now.
- Replacing resources may require to replace dependencies as well.
  This is now the default option for ``replace_resource`` and ``remove_resource``.

0.2b (2014-03-25)
-----------------

- New methods to interact and replace resources.
- ``ResourceRegistry`` objects now keep track of ``fanstatic.Resources`` in ``ResourceRegistry.requirements``,
  rather than file paths.
- ``create_requirement_for`` now figures out proper paths from fanstatic libraries, so just specify proper
  package paths like: ``package_name:some/dir/with/file.js``.


0.1b (2014-03-21)
-----------------

- Initial version
