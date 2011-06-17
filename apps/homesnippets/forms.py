from django.forms import *

class BulkDateForm(Form):
    start_date = DateTimeField(label='Start Date',
                               widget=DateInput(attrs={'class':'datetime'}),
                               required=False)
    end_date = DateTimeField(label='End Date',
                               widget=DateInput(attrs={'class':'datetime'}),
                             required=False)
    ids = CharField(required=True,
                    widget=widgets.HiddenInput())
