from django import forms

from pombola.writeinpublic.client import WriteInPublic


class MessageForm(forms.Form):
    author_name = forms.CharField()
    author_email = forms.CharField()
    subject = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)

    def send_message(self):
        # FIXME: These values should come from config
        client = WriteInPublic("http://10.11.12.13.xip.io:8000", "admin", "123abc")
        r = client.create_message(
            author_name=self.cleaned_data['author_name'],
            author_email=self.cleaned_data['author_email'],
            subject=self.cleaned_data['subject'],
            content=self.cleaned_data['content'],
            # FIXME: This shouldn't be hard-coded
            writeitinstance="/api/v1/instance/3/",
            # FIXME: This shouldn't be hard-coded
            persons=["https://raw.githubusercontent.com/everypolitician/everypolitician-data/master/data/South_Africa/Assembly/ep-popolo-v1.0.json#person-019d1059-be01-44ea-b584-8458d63235c6"],
        )
