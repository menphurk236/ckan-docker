import ckan.plugins.toolkit as tk


@tk.auth_allow_anonymous_access
def doat_get_sum(context, data_dict):
    return {"success": True}


def get_auth_functions():
    return {
        "doat_get_sum": doat_get_sum,
    }
