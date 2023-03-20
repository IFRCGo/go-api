import functools

from django.conf import settings
from django.dispatch import receiver


def suspendingreceiver(signal, **decorator_kwargs):
    """
    A wrapper around the standard django receiver that prevents the receiver
    from running if the setting `SUSPEND_SIGNALS` is `True`.
    This is particularly useful if you want to prevent signals running during
    unit testing.
    @override_settings(SUSPEND_SIGNALS=True)
    class MyTestCase(TestCase):
        def test_method(self):
            Model.objects.create()  # post_save_receiver won't execute
    @suspendingreceiver(post_save, sender=Model)
    def post_save_receiver(sender, instance=None, **kwargs):
        work(instance)
    """

    def our_wrapper(func):
        @receiver(signal, **decorator_kwargs)
        @functools.wraps(func)
        def fake_receiver(sender, **kwargs):
            if settings.SUSPEND_SIGNALS:
                return
            return func(sender, **kwargs)

        return fake_receiver

    return our_wrapper
