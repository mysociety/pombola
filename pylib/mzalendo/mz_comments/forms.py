from django import forms
from django.contrib.comments.forms import CommentForm
from mz_comments.models import CommentWithTitle

class CommentFormWithTitle(CommentForm):
    title = forms.CharField(max_length=300)
    
    def __init__(self, *args, **kwargs):
        super(CommentFormWithTitle, self).__init__(*args, **kwargs)

        # fiddle with the internal ordering so that the title appear at the top
        self.fields.insert( 0, 'title', self.fields['title'] )
        
        # change the name, email and url fields to be hidden
        for f in ['name','email','url']:
            self.fields[f].widget = forms.HiddenInput()

    def get_comment_model(self):
        # Use our custom comment model instead of the built-in one.
        return CommentWithTitle

    def get_comment_create_data(self):
        # Use the data of the superclass, and add in the title field
        data = super(CommentFormWithTitle, self).get_comment_create_data()
        data['title'] = self.cleaned_data['title']
        return data
