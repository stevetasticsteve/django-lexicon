from config.settings import version


def global_template_variables(request):
    return {"version": version}
