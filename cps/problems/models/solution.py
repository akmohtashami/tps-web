# Amir Keivan Mohtashami

from django.db import models
from django.utils.translation import ugettext_lazy as _

from file_repository.models import FileModel
from problems.models import RevisionObject
from problems.models.enums import SolutionVerdict
from problems.models.file import FileNameValidator, get_valid_name
from problems.models.problem import ProblemRevision
from problems.models.testdata import TestCase, Subtask

__all__ = ["Solution", "SolutionSubtaskExpectedScore", "SolutionTestExpectedScore"]


class Solution(RevisionObject):
    _VERDICTS = [(x.name, x.value) for x in list(SolutionVerdict)]

    problem = models.ForeignKey(ProblemRevision, verbose_name=_("problem"))
    name = models.CharField(verbose_name=_("name"), validators=[FileNameValidator], max_length=255, blank=True)
    code = models.ForeignKey(FileModel, verbose_name=_("code"), related_name='+')
    tests_scores = models.ManyToManyField(TestCase, through="SolutionTestExpectedScore")
    subtask_scores = models.ManyToManyField(Subtask, through="SolutionSubtaskExpectedScore")
    # TODO: Should we validate the language here as well?
    language = models.CharField(verbose_name=_("language"), null=True, max_length=20)
    verdict = models.CharField(choices=_VERDICTS, verbose_name=_("verdict"), max_length=50)


    class Meta:
        unique_together = ("problem", "name",)

    def __str__(self):
        return self.name


    def get_language_representation(self):
        choices = [(a, a) for a in self.problem.get_judge().get_supported_languages()]
        for repr, val in choices:
            if self.language == val:
                return repr
        return "Not supported"

    def get_verdict_representation(self):
        return SolutionVerdict.__members__.get(self.verdict, None).value

    def save(self, *args, **kwargs):
        if self.name == "":
            self.name = get_valid_name(self.code.name)

        super(Solution, self).save(*args, **kwargs)


class SolutionSubtaskExpectedScore(RevisionObject):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    subtask = models.ForeignKey(Subtask, verbose_name=_("subtask"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "subtask")
        )


class SolutionTestExpectedScore(RevisionObject):
    solution = models.ForeignKey(Solution, verbose_name=_("solution"))
    testcase = models.ForeignKey(TestCase, verbose_name=_("testcase"))
    score = models.FloatField(verbose_name=_("score"))

    class Meta:
        unique_together = (
            ("solution", "testcase")
        )
