from django.forms import Form, DateTimeField, DateInput, CharField, widgets


class BulkDateForm(Form):
    """Form for changing the start and end dates of many snippets at once"""

    start_date = DateTimeField(label='Start Date',
                               widget=DateInput(attrs={'class': 'datetime'}),
                               required=False)
    end_date = DateTimeField(label='End Date',
                             widget=DateInput(attrs={'class': 'datetime'}),
                             required=False)
    ids = CharField(required=True, widget=widgets.HiddenInput())
