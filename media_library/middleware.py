# media_library/middleware.py
class HTMLSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if this is a request for an HTML site
        if '/html-site/' in request.path:
            # Add CORS headers to allow loading assets
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept'

        return response
