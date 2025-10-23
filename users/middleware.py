import datetime
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)
        max_idle = getattr(settings, 'AUTO_LOGOUT_DELAY', 7200)  # 2 horas
        last_activity = request.session.get('last_activity')
        now = datetime.datetime.now().timestamp()
        if last_activity and now - last_activity > max_idle:
            logout(request)
            messages.info(request, "Has sido desconectado por inactividad.")
        else:
            request.session['last_activity'] = now
        return self.get_response(request)