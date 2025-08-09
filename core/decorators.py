from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('login')}?next={request.path}")

            # allowed_roles can be a string or list/tuple
            roles = allowed_roles if isinstance(allowed_roles, (list, tuple)) else [allowed_roles]

            if request.user.role not in roles:
                return redirect('no_permission')  # your custom no permission URL name

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
