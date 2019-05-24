from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Gradebook


class GradebookForm(forms.ModelForm):
    class Meta:
        model = Gradebook
        fields = ('gb_xls', 'cohort_choices', 'subject_choices',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Upload Gradebook'))
