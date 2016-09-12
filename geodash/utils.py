import yaml

try:
    import simplejson as json
except ImportError:
    import json

from django.template.loader import get_template


def build_state_schema():
    t = "geodash/enumerations.yml"
    y = get_template(t).render({})
    obj = yaml.load(y)
    return obj.get('state_schema', None)


def build_initial_state(dashboard_config, page="dashboard", slug=None):

    initial_state = {
        "page": page,
        "slug": (slug or dashboard_config["slug"]),
        "view": {
            "lat": dashboard_config["view"]["latitude"],
            "lon": dashboard_config["view"]["longitude"],
            "z": dashboard_config["view"]["zoom"],
            "baselayer": dashboard_config["view"].get("baselayer", None),
            "featurelayers": []
        }
    }
    return initial_state


def build_context(config, initial_state, state_schema):
    return {
        "map_config": config,
        "map_config_json": json.dumps(config),
        "state": initial_state,
        "state_json": json.dumps(initial_state),
        "state_schema": state_schema,
        "state_schema_json": json.dumps(state_schema),
        "init_function": "init_dashboard",
        "geodash_main_id": "geodash-main"
    }


def build_dashboard_config(map_obj):
    map_config = yaml.load(map_obj.config)
    map_config["slug"] = map_obj.slug
    map_config["title"]  = map_obj.title
    return map_config


def build_editor_config():
    editor_config_template = "geodashserver/editor.yml"
    editor_config_yml = get_template(editor_config_template).render({})
    editor_config = yaml.load(editor_config_yml)
    return editor_config
