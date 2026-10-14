"""Idempotent setup shared by fresh installation and migration."""

from iran_localization.modules.core.settings import initialize_defaults


def after_install():
	initialize_defaults()
	from iran_localization.modules.banking import setup
	setup()


def after_migrate():
	initialize_defaults()
	from iran_localization.modules.banking import setup
	setup()
