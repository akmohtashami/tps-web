from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.shortcuts import render

from problems.forms.problem import ProblemAddForm
from problems.models import Problem

__all__ = ["ProblemsListView"]


class ProblemsListView(View):

    def get(self, request):
        problems = Problem.objects.all()

        return render(request, "problems/problems_list.html", context={"problems": problems})


class ProblemAddView(View):
    template_name = "problems/add_problem.html"

    def post(self, request):
        form = ProblemAddForm(request.POST, owner=request.user)
        if form.is_valid():
            obj = form.save()
            return HttpResponseRedirect(reverse("problems:overview", kwargs={
                "problem_id": obj.id,
                "revision_slug": obj.get_upstream_fork().get_slug()
            }))

        return render(request, self.template_name, context={"form": form})

    def get(self, request):
        form = ProblemAddForm(owner=request.user)
        return render(request, self.template_name, context={"form": form})
