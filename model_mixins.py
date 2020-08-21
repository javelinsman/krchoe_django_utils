from django.core.serializers import serialize
import json

class Serializable:
    def as_dict(self):
        obj = json.loads(
            serialize('json', [self])
        )[0]
        return {
            **obj['fields'],
            'pk': obj['pk']
        }