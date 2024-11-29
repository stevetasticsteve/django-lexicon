from config.settings.base import version


def global_template_variables(request):
    return {"version": version}
