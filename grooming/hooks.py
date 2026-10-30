# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-install hook for grooming module.
    """
    _logger.info("Grooming module installed successfully!")


def uninstall_hook(env):
    """
    Uninstall hook for grooming module.
    """
    _logger.info("Grooming module uninstalled.")
