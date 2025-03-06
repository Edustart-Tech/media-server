from django.utils.deprecation import MiddlewareMixin


class CrossOriginOpenerPolicyMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    # def process_response(self, request, response):
    #     response['Cross-Origin-Opener-Policy'] = 'unsafe-none'  # or 'unsafe-none' or 'same-origin-allow-popups'
    #     return response

    def __call__(self, request):
        response = self.get_response(request)

        # Allow all origins or specify the origins you want
        response['Access-Control-Allow-Origin'] = '*'  # Allow all origins, or specify an origin like 'http://localhost:8001'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'  # Allowed methods
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'  # Allowed headers

        return response