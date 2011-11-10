import urllib
import textwrap

from django import http
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts  import render_to_response, get_object_or_404, redirect
from django.shortcuts import render_to_response
from django.template   import RequestContext
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic.list_detail import object_detail, object_list

from comments2.forms import CommentForm
from comments2.models import Comment, CommentFlag

def get_object(module_name, slug):
    # retrieve the content_type that we need
    ct = get_object_or_404( ContentType, model=module_name )

    # retrieve the object
    obj = get_object_or_404( ct.model_class(), slug=slug )

    return obj
    

def list_for(request, module_name, slug):
    """Display comments"""

    obj = get_object( module_name, slug )

    return render_to_response(
        'comments/list_for.html',
        {
            'object': obj,
        },
        context_instance=RequestContext(request)
    )



@login_required
@csrf_protect
def add(request, module_name, slug):

    obj = get_object( module_name, slug )
    comment = False

    if request.method == 'POST':
        form = CommentForm(obj, request.POST)
        if form.is_valid():
            comment = form.get_comment_object()
            comment.ip_address = request.META['REMOTE_ADDR']
            comment.user = request.user
            comment.save()
            
            return redirect( comment )
            
    else:
        form = CommentForm(obj)

    return render_to_response(
        'comments/add.html',
        {
            'object': obj,
            'form':   form,
            'comment': comment,
        },
        context_instance=RequestContext(request)
    )

@csrf_protect
def flag(request, comment_id):

    comment = get_object_or_404( Comment, id=comment_id )
    flag    = False

    # Flag the comment for a post
    if request.method == 'POST':
        if request.user.is_authenticated():
            flag, created = CommentFlag.objects.get_or_create(
                user = request.user,
                comment = comment,
            )
        else:
            flag = CommentFlag.objects.create( comment=comment )
            
    return render_to_response(
        'comments/flag.html',
        {
            'comment': comment,
            'flag': flag,
        },
        context_instance=RequestContext(request)
    )


def view(request, comment_id):
    """
    Show one comment - even if it is not approved yet.

    This view is used so that people can tweet their comments. If the comment is
    approved, on not yet moderated show it. If it has been rejected don't show
    it. If it does not exist 404.

    FUTURE: Once the smarts are in place the template should actually redirect
    us to the object's page and then scroll us to the comment for approved
    comments.
    """

    comment = get_object_or_404( Comment, id=comment_id )

    comment_rejected = comment.status == 'rejected'
            
    return render_to_response(
        'comments/view.html',
        {
            'comment': comment,
            'comment_rejected': comment_rejected,
        },
        context_instance=RequestContext(request)
    )
    