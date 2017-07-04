import re
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest ,JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from markupsafe import Markup

from aitrading.models import AuthorizedUser
from django.contrib.auth.models import User
from aitrading.morningstar_crawler import find_by_isin, find_by_ticker

from registration.backends.hmac.views import RegistrationView

@login_required
def trade(request):
    return render(request, 'trade.html')


def no_script(request):
    redir = request.GET.get('redirect', '/')

    # Prevent erroneous redirects
    if redir[0] != '/':
        redir = '/'

    return render(request, 'noscript.html',
                  {'redirect': Markup('window.location.replace("%s");' % redir)})


@login_required
def security_search(request, method):
    if method == 'isin':
        return JsonResponse(find_by_isin(request.GET.get('isin'), request.GET.get('currency')))
    elif method == 'ticker':
        return JsonResponse(find_by_ticker(request.GET.get('ticker'), request.GET.get('currency')))
    else:
        return HttpResponseNotFound('<h1>Cannot search by "%s"</h1>' % method)

def check_authorized_email(request):
    email = request.POST.get('email')
    if email is None or len(email) == 0:
        return HttpResponseBadRequest('No email provided')
    else:
        if User.objects.filter(email=email).count() > 0:
            return HttpResponseBadRequest('An account with this email address already exists')

        try:
            return HttpResponse(AuthorizedUser.objects.get(email=email).account)
        except AuthorizedUser.DoesNotExist:
            return HttpResponseNotFound('This address has not been authorized to use AI Trading.'+
                                          ' Please contact the supervisor to request access.')


# Overrides default inactive user creator in registration.backends.hmac.views.RegistrationView
def create_inactive_user(self, form):
    new_user = form.save(commit=False)
    new_user.first_name = re.sub(r'[^a-zàâçéèêëîïôûùüÿñæœ \'-]/gi', '', form.data.get('first_name'))
    new_user.last_name = re.sub(r'[^a-zàâçéèêëîïôûùüÿñæœ \'-]/gi', '', form.data.get('last_name'))
    new_user.is_active = False
    new_user.save()

    self.send_activation_email(new_user)

    return new_user

RegistrationView.create_inactive_user = create_inactive_user