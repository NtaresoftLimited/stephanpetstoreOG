def post_init_hook(env):
    """Apply SKY access to the existing branch cashier and POS manager users."""
    cashier_group = env.ref("sky_dashboard.group_sky_stock_cashier")
    manager_group = env.ref("sky_dashboard.group_sky_stock_manager")

    # Grant cashier access to all active POS users and config employees
    configs = env["pos.config"].sudo().search([("active", "=", True)])
    employees = configs.mapped("basic_employee_ids") | configs.mapped("advanced_employee_ids")
    cashier_users = employees.mapped("user_id").filtered(lambda user: user.active)

    pos_user_group = env.ref("point_of_sale.group_pos_user")
    all_pos_users = env["res.users"].sudo().search(
        [("groups_id", "in", pos_user_group.id), ("active", "=", True)]
    )
    (cashier_users | all_pos_users).write({"groups_id": [(4, cashier_group.id)]})

    pos_manager_group = env.ref("point_of_sale.group_pos_manager")
    pos_managers = env["res.users"].sudo().search(
        [("groups_id", "in", pos_manager_group.id), ("active", "=", True)]
    )
    pos_managers.write({"groups_id": [(4, manager_group.id)]})
