from django import forms

from problems.models import ProblemData


class OverviewForm(forms.ModelForm):
    class Meta:
        model = ProblemData
        exclude = ['checker', 'problem', 'title']

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem")
        self.revision = kwargs.pop("revision")
        super(OverviewForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'code_name',
            'task_type',
            'task_type_parameters',
            'score_type',
            'score_type_parameters',
            'time_limit',
            'memory_limit']

    def save(self, commit=True):
        super(OverviewForm, self).save(commit=False)
        if commit:
            self.instance.save()
            self.save_m2m()