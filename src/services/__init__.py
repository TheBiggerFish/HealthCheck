
from .httpservice import HttpService
from .mcservice import MinecraftService
from .service import Service

service_mapping = {
    'http': HttpService,
    'minecraft': MinecraftService,
}
