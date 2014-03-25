Changelog
=========

0.2b (Unreleased)
-----------------

- New methods to interact and replace resources.
- ``ResourceRegistry`` objects now keep track of ``fanstatic.Resources`` in ``ResourceRegistry.requirements``,
  rather than file paths.
- ``create_requirement_for`` now figures out proper paths from fanstatic libraries, so just specify proper
  package paths like: ``package_name:some/dir/with/file.js``.


0.1b (2014-03-21)
-----------------

- Initial version
