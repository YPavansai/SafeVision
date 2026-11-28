import logging
import time

perf_logger = logging.getLogger('safevision.performance')
sec_logger = logging.getLogger('safevision.security')


class RequestLoggingMiddleware:
    """
    Measures API latency, attaches X-Response-Time-Ms, and logs security/error events
    without ever recording sensitive credentials, tokens, or request bodies.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        response['X-Response-Time-Ms'] = str(duration_ms)

        user_label = (
            request.user.username
            if hasattr(request, 'user') and getattr(request.user, 'is_authenticated', False)
            else 'anonymous'
        )
        remote_ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '-')
        )

        if response.status_code in (401, 403, 429):
            sec_logger.warning(
                "security_event status=%s method=%s path=%s user=%s ip=%s duration_ms=%s",
                response.status_code, request.method, request.path, user_label, remote_ip, duration_ms
            )
        elif response.status_code >= 500:
            perf_logger.error(
                "server_error status=%s method=%s path=%s user=%s duration_ms=%s",
                response.status_code, request.method, request.path, user_label, duration_ms
            )
        elif request.path.startswith('/api/'):
            perf_logger.info(
                "api_request status=%s method=%s path=%s user=%s duration_ms=%s",
                response.status_code, request.method, request.path, user_label, duration_ms
            )
        return response
