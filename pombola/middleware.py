from instances.models import Instance

class FakeInstanceMiddleware:
    """
    We don't really use instances, as we're embedding sayit as an app. It
    should really be factored out, but for now, just use the default one
    created by the initial migration.
    """
    def process_request(self, request):
        request.instance, _ = Instance.objects.get_or_create(label='default')
        request.is_user_instance = request.user.is_authenticated() and ( request.instance in request.user.instances.all() or request.user.is_superuser )
