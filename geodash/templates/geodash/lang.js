{% load i18n %}

if (window.GeoExt && GeoExt.Lang) {
    GeoExt.Lang.set("{{ LANGUAGE_CODE }}");
}

if (window.Embed) {
  Ext.apply(Embed.prototype, {
      zoomLevelText: gettext("Zoom Level {zoom}")
  });
}

{% block extra_lang %}
{% endblock %}
