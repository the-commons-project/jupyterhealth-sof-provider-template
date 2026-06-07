c.SMARTExtensionApp.client_id = "{{ cookiecutter.client_id }}"
c.ServerApp.tornado_settings = {
    "headers": {
        "Content-Security-Policy": "frame-ancestors 'self' {{ cookiecutter.epic_iframe_origin }}"
    }
}
