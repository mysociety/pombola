from disqus.wxr_feed import ContribCommentsWxrFeed
# from comments2.models import Comment
from core.models import Person


# http://help.disqus.com/customer/portal/articles/472150-custom-xml-import-format

class CommentWxrFeed(ContribCommentsWxrFeed):
    link = "/"

    def items(self):
        return Person.objects.all()[:5] # remove [:5] before generating full dump

    def item_pubdate(self, item):
        return item.created

    def item_description(self, item):
        return str(item)

    def item_guid(self, item):
        # set to none so that the output dsq:thread_identifier is empty
        return None

    def item_comments(self, item):
        return item.comments.all()
    
    def comment_user_name(self, comment):
        return str(comment.user)

    def comment_user_email(self, comment):
        return comment.user.email or str(comment.id) + '@bogus-email-address.com'

    def comment_user_url(self, comment):
        return None

    def comment_is_approved(self, comment):
        return 1