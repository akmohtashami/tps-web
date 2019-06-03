import logging
from functools import update_wrapper

import magic
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import classonlymethod
from django.views.generic import View

from file_repository.models import FileModel
from problems.views.utils import extract_revision_data, get_git_object_or_404
from problems.models import SourceFile, NewProblemBranch
from django.utils.translation import ugettext as _

from django.db.models import ObjectDoesNotExist

from git_orm import transaction as git_transaction, GitError
from pygit2 import Signature

__all__ = ["ProblemObjectView", "ProblemObjectDeleteView", "RevisionObjectView",
           "ProblemObjectAddView", "ProblemObjectEditView",
           "ProblemObjectShowSourceView", "ProblemObjectDownloadView", ]

logger = logging.getLogger('django.request')

class ProblemObjectView(View):
    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.
        """
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError("You tried to pass in the %s method name as a "
                                "keyword argument to %s(). Don't do that."
                                % (key, cls.__name__))
            if not hasattr(cls, key):
                raise TypeError("%s() received an invalid keyword %r. as_view "
                                "only accepts arguments that are already "
                                "attributes of the class." % (cls.__name__, key))

        def view(request, problem_code, revision_slug, *args, **kwargs):
            self = cls(**initkwargs)
            if hasattr(self, 'get') and not hasattr(self, 'head'):
                self.head = self.get
            self.request = request
            self.args = args
            self.kwargs = kwargs
            self.revision_slug = revision_slug

            self.problem, self.branch, self.revision = \
                extract_revision_data(problem_code, revision_slug, request.user)

            git_transaction.set_default_transaction(self.revision._transaction)

            #  TODO: set git repo path here

            return self.dispatch(request, problem_code, revision_slug, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(ProblemObjectView, self).dispatch(request, *args, **kwargs)
        except Http404:
            raise
        except Exception as e:
            if not settings.DEBUG:
                return self.exception_occured(request, e, *args, **kwargs)
            else:
                raise e

    def exception_occured(self, request, exception, *args, **kwargs):
        logger.error(
            'Exception occured (%s) %s: %s', request.method, request.path,
            str(exception),
            extra={
                'request': request,
                'exception': exception,
            },
            exc_info=exception,
        )
        return render(request, "problems/exception.html", context={
            "exception": str(exception)
        })


class RevisionObjectView(ProblemObjectView):
    http_method_names_requiring_edit_access = ['post', 'put', 'delete', 'patch']
    UPDATED_TO_GIT = False

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names_requiring_edit_access and \
                not self.edit_allowed():
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(RevisionObjectView, self).dispatch(request, *args, **kwargs)

    def _allowed_methods(self):
        allowed_methods = super(RevisionObjectView, self)._allowed_methods()

        if not self.edit_allowed():
            allowed_methods = [allowed_method for allowed_method in allowed_methods
                               if allowed_method not in self.http_method_names_requiring_edit_access]

        return allowed_methods

    def edit_allowed(self):
        if self.branch is None:
            return False
        if not(self.revision.editable(self.request.user)):
            return False
        # TODO: Remove this after everything is updated
        if not self.UPDATED_TO_GIT:
            return False
        return True


class ProblemObjectDeleteView(RevisionObjectView):
    object_type = None
    permissions_required = []
    redirect_to = None
    lookup_field_name = "id"
    url_slug = "object_id"
    revision_field_name = "problem"

    def delete(self, request, problem_code, revision_slug, *args, **kwargs):
        object_id = kwargs.pop(self.url_slug, args[0] if len(args) > 0 else None)
        if not self.object_type:
            raise ImproperlyConfigured("you must specify an object type for delete view")
        if not self.redirect_to:
            raise ImproperlyConfigured("you must specify a url for redirect to after delete")
        obj = get_object_or_404(self.object_type, **{
            self.revision_field_name: self.revision,
            self.lookup_field_name: object_id
        })
        obj.delete()
        return HttpResponseRedirect(reverse(self.redirect_to, kwargs={
            "problem_code": self.problem.code,
            "revision_slug": revision_slug
        }))

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class ProblemObjectAddView(RevisionObjectView):
    template_name = None
    model_form = None
    required_permissions = []
    http_method_names_requiring_edit_access = \
        ['get'] + \
        RevisionObjectView.http_method_names_requiring_edit_access

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def __init__(self, **kwargs):
        super(ProblemObjectAddView, self).__init__(**kwargs)
        self._check_values()

    def _show_form(self, request, form):
        return render(request, self.template_name, context={
            "form": form
        })

    def post(self, request, problem_code, revision_slug, *args, **kwargs):
        form = self.model_form(request.POST, request.FILES,
                               problem=self.problem,
                               revision=self.revision,
                               owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(self.get_success_url(request, problem_code, revision_slug, obj))
        return self._show_form(request, form)

    def get(self, request, problem_code, revision_slug, *args, **kwargs):
        form = self.model_form(problem=self.problem,
                               revision=self.revision,
                               owner=request.user)
        return self._show_form(request, form)

    def get_success_url(self, request, problem_code, revision_slug, obj):
        raise NotImplementedError("Thist must be implemented in subclasses")


class ProblemObjectEditView(RevisionObjectView):
    template_name = None
    model_form = None
    permissions_required = []
    http_method_names_requiring_edit_access = \
        ['get'] + \
        RevisionObjectView.http_method_names_requiring_edit_access

    def _check_values(self):
        assert self.template_name is not None
        assert self.model_form is not None

    def _show_form(self, request, form, instance):
        return render(request, self.template_name, context={
            "form": form,
            "instance": instance,
        })

    def post(self, request, problem_code, revision_slug, *args, **kwargs):
        if "_commit_id" not in request.POST:
            raise PermissionDenied
        if settings.DISABLE_BRANCHES:
            edited_on_commit_id = request.POST["_commit_id"]
            patch_prefix = "{}_patch".format(request.user.username)
            patch_number = 0
            for x in NewProblemBranch.objects.filter(
                name__startswith=patch_prefix
            ):
                try:
                    patch_number = max(patch_number, int(x.name[len(patch_prefix):]))
                except ValueError:
                    pass
            new_branch_name = patch_prefix + str(patch_number + 1)
            new_branch = self.problem.branches.create(
                name=new_branch_name,
                head=edited_on_commit_id
            )

            overriding_transaction = git_transaction.Transaction(
                repository_path=self.problem.repository_path,
                branch_name=new_branch_name
            )
            previous_transaction = git_transaction.current()
        else:
            raise NotImplementedError

        git_transaction.set_default_transaction(overriding_transaction)

        try:
            instance = self.get_instance(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404

        form = self.model_form(request.POST, request.FILES,
                               problem=self.problem,
                               revision=self.revision,
                               owner=request.user,
                               instance=instance)
        if form.is_valid():
            obj = form.save()
            if hasattr(obj, "_transaction"):
                new_commit = obj._transaction.commit(
                    author_signature=Signature(
                        request.user.get_full_name(),
                        request.user.email
                    )
                )
                if settings.DISABLE_BRANCHES:
                    try:
                        previous_transaction.merge(new_commit, squash=True, author_signature=Signature(
                            request.user.get_full_name(),
                            request.user.email
                        ))
                    except GitError as e:
                        messages.error(request, _("Unable to merge automatically. "
                                                  "Your changes can be found in commit {commit_id}. "
                                                  "The merge should be done manually.").format(
                            commit_id=str(new_commit)
                        ))
                        return HttpResponseRedirect(self.request.get_full_path())
                    new_branch.delete()
            messages.success(request, _("Saved successfully"))
            return HttpResponseRedirect(self.get_success_url(request, problem_code, revision_slug, obj))
        return self._show_form(request, form, instance)

    def get(self, request, problem_code, revision_slug, *args, **kwargs):
        try:
            instance = self.get_instance(request, *args, **kwargs)
        except ObjectDoesNotExist:
            raise Http404

        form = self.model_form(problem=self.problem,
                               revision=self.revision,
                               owner=request.user,
                               instance=instance)
        return self._show_form(request, form, instance)

    def get_success_url(self, request, problem_code, revision_slug, obj):
        raise NotImplementedError("This must be implemented in subclasses")

    def get_instance(self, request, *args, **kwargs):
        raise NotImplementedError("This must be implemented in subclasses")


class ProblemObjectShowSourceView(RevisionObjectView):
    instance_slug = None
    model = None
    template_name = "problems/view_source.html"
    language_field_name = None
    code_field_name = None

    def post(self, request, problem_code, revision_slug, **kwargs):
        instance_pk = kwargs.get(self.instance_slug)
        instance = get_git_object_or_404(self.model, pk=instance_pk, problem=self.revision)
        code_file = getattr(instance, self.code_field_name)
        if "source_code" in request.POST:
            new_file = FileModel()
            new_file.file.save(code_file.name, ContentFile(request.POST["source_code"]))
            setattr(instance, self.code_field_name, new_file)
            instance.save()
            if isinstance(self, SourceFile):
                self.invalidate_compilation()
            messages.success(request, _("Saved successfully"))
        return HttpResponseRedirect(request.get_full_path())

    def get(self, request, problem_code, revision_slug, **kwargs):
        instance_pk = kwargs.get(self.instance_slug)
        instance = get_git_object_or_404(self.model, pk=instance_pk, problem=self.revision)
        code_file = getattr(instance, self.code_field_name)
        file_ = code_file.file
        file_.open()
        code = file_.read()
        lang = getattr(instance, self.language_field_name)
        title = str(instance)
        return render(request, self.template_name, context={
            "code": code,
            "lang": lang,
            "title": title,
            "next_url": self.get_next_url(request, problem_code, revision_slug, instance)
        })

    def get_next_url(self, request, problem_code, revision_slug, obj):
        raise NotImplementedError("Must be implemented in subclasses")


class ProblemObjectDownloadView(RevisionObjectView):
    http_method_names_requiring_edit_access = []

    def get_file(self, request, *args, **kwargs):
        raise NotImplementedError("Must be implemented in subclasses")

    def get_name(self, request, *args, **kwargs):
        raise NotImplementedError("Must be implemented in subclasses")

    def get(self, request, *args, **kwargs):
        file_ = self.get_file(request, *args, **kwargs)
        file_.open()
        content_type = magic.from_buffer(file_.read(1024), mime=True)
        file_.open()
        response = HttpResponse(file_, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s' % self.get_name(request, *args, **kwargs)

        return response
