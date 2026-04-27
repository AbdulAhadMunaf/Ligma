from django.http import Http404
from django.shortcuts import get_list_or_404 as _get_list_or_404
from django.shortcuts import get_object_or_404 as _get_object_or_404

from utils.exceptions.errors import CoreResourceNotFoundError
from utils.exceptions.exceptions import CoreException


def get_object_by_pk_or_404(klass, pk, klass_name=None, custom_message=None):
    try:
        return _get_object_or_404(klass, pk=pk)
    except Http404:
        klass_name = "Resource" if klass_name is None else klass_name
        custom_message = (
            f"{klass_name} Not Found" if custom_message is None else custom_message
        )
        raise CoreException(
            CoreResourceNotFoundError.RESOURCE_NOT_FOUND_CUSTOM_MSG,
            custom_message,
        )


def get_list_by_pk_or_404(klass, pk, klass_name=None, custom_message=None):
    try:
        return _get_list_or_404(klass, pk=pk)
    except Http404:
        klass_name = "Resource" if klass_name is None else klass_name
        custom_message = (
            f"{klass_name} Not Found" if custom_message is None else custom_message
        )
        raise CoreException(
            CoreResourceNotFoundError.RESOURCE_NOT_FOUND_CUSTOM_MSG,
            custom_message,
        )
