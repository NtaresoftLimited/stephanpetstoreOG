# -*- coding: utf-8 -*-
from . import controllers, models

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    setup_provider(env, "sky_wallet")
    env["payment.provider"]._sky_wallet_link_journal()


def uninstall_hook(env):
    reset_payment_provider(env, "sky_wallet")
