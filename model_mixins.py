from django.core.serializers import serialize
import json

class Serializable:
    def as_dict(self):
        return json.loads(
            serialize('json', [self])
        )[0]