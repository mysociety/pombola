from mz_comments.models import CommentWithTitle
from mz_comments.forms import CommentFormWithTitle

def get_model():
    return CommentWithTitle

def get_form():
    return CommentFormWithTitle
