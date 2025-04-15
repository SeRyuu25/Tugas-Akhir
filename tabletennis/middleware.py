from django.utils import translation

# Buat paksa jadi bahasa Indonesia (UInya)
class ForceIndonesianMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        translation.activate('id')
        response = self.get_response(request)
        translation.deactivate()
        return response
