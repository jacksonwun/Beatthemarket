from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path, re_path
from django.core.asgi import get_asgi_application
from warrant.consumers import WarrantConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack(
			URLRouter([
					path('warrant/', WarrantConsumer.as_asgi()),
			])
		)
	),
})