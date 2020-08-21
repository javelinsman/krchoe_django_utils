from django.http import JsonResponse
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from django.core.exceptions import SuspiciousOperation
from django.views.generic.list import BaseListView

import json

class JsonBaseView(View):
    @property
    def form_data(self):
        return json.loads(self.request.body)

    def dispatch(self, *args, **kwargs):
        try: 
            obj = super().dispatch(*args, **kwargs)
            return JsonResponse({
                'payload': obj
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            })

class JsonListView(BaseListView):
    def render_to_response(self, context, **response_kwargs):
        return JsonResponse({
            'payload': self.as_serializable(
                context['object_list']
            ),
            **response_kwargs
        })

    def as_serializable(self, model_objects):
        return [
            model_object.as_dict()
            for model_object in model_objects
        ]

class JsonCRUDView(SingleObjectMixin, View):
    def render_to_response(self, context, **response_kwargs):
        return JsonResponse({
            'payload': self.as_serializable(context),
            **response_kwargs
        })

    def as_serializable(self, model_object):
        if type(model_object) == dict:
            return model_object
        return model_object.as_dict()

    def get_form_data(self, request):
        return json.loads(request.body)

    def raise_400(self):
        raise SuspiciousOperation()

    def get(self, request, *args, **kwargs):
        if self.pk_url_kwarg not in kwargs:
            self.raise_400()
        return self.render_to_response(self.get_object())

    def post(self, request, *args, **kwargs):
        obj = self.model(**self.get_form_data(request))
        self.object = obj
        self.object.save()
        obj_retrieved_again = self.model.objects.get(pk=self.object.pk)
        return self.render_to_response(obj_retrieved_again)

    def put(self, request, *args, **kwargs):
        if self.pk_url_kwarg not in kwargs:
            self.raise_400()
        obj = self.get_object()
        form_data = self.get_form_data(request)
        for key, value in form_data.items():
            setattr(obj, key, value)
        obj.save()
        obj_retrieved_again = self.model.objects.get(pk=obj.pk)
        return self.render_to_response(obj_retrieved_again)

    def delete(self, request, *args, **kwargs):
        if self.pk_url_kwarg not in kwargs:
            self.raise_400()
        pk = kwargs[self.pk_url_kwarg]
        obj = self.get_object()
        obj.delete()
        return self.render_to_response({'id': pk})

class JsonRelationCRUDView(SingleObjectMixin, View):
    target_model = None
    field_name = 'targets'

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse({
            'payload': self.as_serializable(context),
            **response_kwargs
        })

    def as_serializable(self, model_object):
        if type(model_object) == dict:
            return model_object
        return model_object.as_dict()

    def get_ids_from_form(self, request):
        return json.loads(request.body)['pks']

    def get_target_objects(self, request):
        target_pks = self.get_ids_from_form(request)
        return self.target_model.objects.filter(pk__in=target_pks)

    def post(self, request, pk, *args, **kwargs):
        self.object = self.get_object()
        target_objs = self.get_target_objects(request)
        getattr(self.object, self.field_name).add(*target_objs)
        self.object.save()
        return self.render_to_response(self.object)

    def put(self, request, pk, *args, **kwargs):
        return self.post(request, pk, *args, **kwargs)

    def delete(self, request, pk, *args, **kwargs):
        self.object = self.get_object()
        target_objs = self.get_target_objects(request)
        getattr(self.object, self.field_name).remove(*target_objs)
        self.object.save()
        return self.render_to_response(self.object)