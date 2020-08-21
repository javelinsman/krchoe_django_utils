from django.http import JsonResponse
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin
from django.core.exceptions import SuspiciousOperation
from django.db.models.query import QuerySet
import logging

import json

class PublicError(SuspiciousOperation):
    pass

class JsonBaseView(View):
    @property
    def form_data(self):
        return json.loads(self.request.body)

    def raise_public_error(self, message):
        raise PublicError(message)

    def as_serializable(self, obj):
        if hasattr(obj, 'as_dict'):
            return obj.as_dict()
        elif type(obj) == dict:
            return {
                key: self.as_serializable(value)
                for key, value in obj.items()
            }
        elif type(obj) == list or isinstance(obj, QuerySet):
            return [
                self.as_serializable(value)
                for value in obj
            ]
        else:
            return obj

    def dispatch(self, *args, **kwargs):
        try: 
            obj = super().dispatch(*args, **kwargs)
            return JsonResponse({
                'payload': self.as_serializable(obj)
            })
        except PublicError as e:
            return JsonResponse({
                'error': str(e)
            })
        # except Exception as e:
        #     logging.info(e)
        #     print(e)
        #     e.stacktrace()
        #     return JsonResponse({
        #         'error': 'internal server error occured'
        #     })

class JsonListView(JsonBaseView, MultipleObjectMixin):
    def get_objects(self):
        # modified django's BaseListView.get
        # https://github.com/django/django/blob/master/django/views/generic/list.py#L139
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()

        if not allow_empty:
            if self.get_paginate_by(self.object_list) is not None and hasattr(self.object_list, 'exists'):
                is_empty = not self.object_list.exists()
            else:
                is_empty = not self.object_list
            if is_empty:
                raise Http404(_('Empty list and “%(class_name)s.allow_empty” is False.') % {
                    'class_name': self.__class__.__name__,
                })
        context = self.get_context_data()
        return context['object_list']

    def get(self, request, *args, **kwargs):
        return self.get_objects()

class JsonSingleObjectView(JsonBaseView, SingleObjectMixin):
    # you can use self.get_object() defined in SingleObjectMixin
    pass

class JsonCRUDView(JsonSingleObjectView):
    allowed_params = None

    def get(self, request, *args, **kwargs):
        self.assert_pk_specified(**kwargs)
        return self.get_object()

    def post(self, request, *args, **kwargs):
        return self.create_or_update_object()

    def put(self, request, *args, **kwargs):
        self.assert_pk_specified(**kwargs)
        obj = self.get_object()
        return self.create_or_update_object(obj)

    def delete(self, request, *args, **kwargs):
        self.assert_pk_specified(**kwargs)
        pk = kwargs[self.pk_url_kwarg]
        obj = self.get_object()
        obj.delete()
        return self.render_to_response({'id': pk})

    def create_or_update_object(self, obj=None):
        if obj is None:
            obj = self.model()
        if self.allowed_params is None:
            for key, value in form_data.items():
                setattr(obj, key, value)
        else:
            for key, value in form_data.items():
                if key in self.allowed_params:
                    setattr(obj, key, value)
        # object should be retrieved again to have it in standard form
        # ex. '2020-08-21...' in DateTimeField becomes datetime.datetime
        return self.model.objects.get(pk=obj.pk)

    def assert_pk_specified(self, **kwargs):
        if self.pk_url_kwarg not in kwargs:
            self.raise_public_error(
                f'{self.pk_url_kwarg} is not specified'
            )

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