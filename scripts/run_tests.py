"""Run module and database integration tests against an explicitly selected test site."""

import argparse
import os
import sys
import unittest
from pathlib import Path

import frappe


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--site", required=True, help="Existing disposable Frappe test site")
	parser.add_argument("--sites-path", default="sites")
	args = parser.parse_args()
	sites = Path(args.sites_path).resolve()
	os.chdir(sites)
	frappe.init(site=args.site, sites_path=str(sites))
	frappe.connect()
	frappe.set_user("Administrator")
	try:
		suite = unittest.defaultTestLoader.loadTestsFromNames(
			[
				"iran_localization.tests.test_modules",
				"iran_localization.tests.test_site",
			]
		)
		result = unittest.TextTestRunner(verbosity=2).run(suite)
		return 0 if result.wasSuccessful() else 1
	finally:
		frappe.db.rollback()
		frappe.destroy()


if __name__ == "__main__":
	sys.exit(main())
