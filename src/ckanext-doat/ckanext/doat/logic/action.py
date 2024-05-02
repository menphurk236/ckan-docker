import ckan.plugins.toolkit as tk
import ckanext.doat.logic.schema as schema


@tk.side_effect_free
def doat_get_sum(context, data_dict):
    tk.check_access(
        "doat_get_sum", context, data_dict)
    data, errors = tk.navl_validate(
        data_dict, schema.doat_get_sum(), context)

    if errors:
        raise tk.ValidationError(errors)

    return {
        "left": data["left"],
        "right": data["right"],
        "sum": data["left"] + data["right"]
    }


def get_actions():
    return {
        'doat_get_sum': doat_get_sum,
    }
