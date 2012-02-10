Version 0.3.2
=============

- Mostly bug fixes, see commits.

Version 0.3.1
=============

- Use ``--distribute`` with ``virtualenv.create``.
- Add new command ``fabd.create_configs``.
- Don't override ``conf_name`` in ``fabd.conf``.

Version 0.3.0
=============

- Now Configuration is based on class DefaultConf.
- Added new command ``virtualenv.make_relocatable``.
- Added new commands to work with versions (see ``fabdeploy.version``).
- ``src_path`` and ``env_path`` now contain ``version``.
- ``supervisord_config_template`` was renamed to
  ``supervisord_config_lfile``. ``supervisord_config`` was renamed to
  ``superfisord_config_file``.
- ``backups_path`` renamed to ``backup_path``.
