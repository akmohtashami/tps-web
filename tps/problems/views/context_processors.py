import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q

from problems.models import MergeRequest
from problems.models.enums import SolutionVerdict
from .utils import extract_revision_data

logger = logging.getLogger(__name__)

def revision_data(request):
    if "problem_code" not in request.resolver_match.kwargs:
        return {}
    problem_code = request.resolver_match.kwargs["problem_code"]
    revision_slug = request.resolver_match.kwargs["revision_slug"]
    problem, branch, revision = extract_revision_data(problem_code, revision_slug, request.user)
    revision_editable = False

    errors = {}
    try:
        errors["testcase"] = revision.testcase_set.all().count()
        if revision.solution_set.filter(verdict=SolutionVerdict.model_solution).exists():
            errors["solution"] = 0
        else:
            errors["solution"] = 1
        """
        invocations = revision.solutionrun_set.all()
        failed_invocations = 0
        for invocation in invocations:
            if not invocation.validate():
                failed_invocations += 1
        errors["invocation"] = failed_invocations
        """
        if revision.problem_data.checker is None:
            errors["checker"] = 1
        else:
            errors["checker"] = 0
        if not revision.validator_set.all().exists():
            errors["validator"] = 1
        else:
            errors["validator"] = 0
        errors["discussion"] = problem.discussions.filter(closed=False).count()
        errors["merge_requests"] = problem.merge_requests.filter(status=MergeRequest.OPEN).count()
    except Exception as e:
        logger.error(e, exc_info=e)
    branches = problem.branches.all()
    return {
        "problem": problem,
        "revision": revision,
        "branch": branch,
        "branches": branches,
        "revision_slug": revision_slug,
        "commit_editable": branch is not None and False,
        "revision_editable": revision_editable,
        "branches_disabled": getattr(settings, "DISABLE_BRANCHES", False),
        "errors": errors
    }
