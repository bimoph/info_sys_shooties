from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    user_role = request.user.role
    return render(request, 'core/home.html', {'role': user_role})

def no_permission(request):
    return render(request, 'core/no_permission.html', status=403)