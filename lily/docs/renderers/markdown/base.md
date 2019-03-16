
# CoSphere API

CoSphere's API with hypermedia links

{% for tag, tag_spec in document_tree.items %}
## {{ tag | safe  }}

{% for command_spec in tag_spec %}

### {{ command_spec.title | safe }}

{{ command_spec.description | safe  }}

{% for call in command_spec.calls %}

#### {{ call.title | safe  }}

Request:

```http
{{ call.request.method | upper }} {{ call.request.path | safe }} HTTP/1.1

{% for header, value in call.request.headers.items %}
{{ header }}: {{ value }}
{% endfor %}

{% if call.request.content %}
{{ call.request.content | safe }}
{% endif %}

```

Respone:

```json
{{ call.response.content | safe }}
```

{% endfor %}
{% endfor %}
{% endfor %}
