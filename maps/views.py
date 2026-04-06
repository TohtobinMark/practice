from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import Location, DistributionRequest, Service, ServiceCategory, License
from .forms import LocationForm, DistributionRequestForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def home(request):
    clients = Location.objects.all()

    requests = DistributionRequest.objects.exclude(status__in=['completed', 'rejected'])

    user_request = None
    if request.user.is_authenticated:
        user_request = DistributionRequest.objects.filter(
            user=request.user
        ).exclude(status__in=['completed', 'rejected']).first()

        service_categories = ServiceCategory.objects.all().prefetch_related('service_set')
        services = Service.objects.all()
        licenses = License.objects.all()

        context = {
            'clients': clients,
            'requests': requests,
            'user_request': user_request,
            'services': services,
            'service_categories': service_categories,
            'licenses': licenses,
            'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
        }
        return render(request, 'maps/home.html', context)


@login_required
def add_location(request):
    """Добавление нового маркера (клиента/объекта)"""
    initial_data = {}
    if 'lat' in request.GET and 'lon' in request.GET:
        try:
            initial_data['latitude'] = float(request.GET.get('lat'))
            initial_data['longitude'] = float(request.GET.get('lon'))
        except (ValueError, TypeError):
            pass

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.user = request.user
            location.save()
            messages.success(request, f'Маркер "{location.title}" успешно добавлен!')
            return redirect('home')
    else:
        form = LocationForm(initial=initial_data)

    return render(request, 'maps/location_form.html', {'form': form, 'title': 'Добавить маркер'})


@login_required
def edit_location(request, pk):
    """Редактирование маркера"""
    location = get_object_or_404(Location, pk=pk, user=request.user)

    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, f'Маркер "{location.title}" успешно обновлен!')
            return redirect('home')
    else:
        form = LocationForm(instance=location)

    return render(request, 'maps/location_form.html',
                  {'form': form, 'title': 'Редактировать маркер', 'location': location})


@login_required
def delete_location(request, pk):
    """Удаление маркера"""
    location = get_object_or_404(Location, pk=pk, user=request.user)

    if request.method == 'POST':
        location_title = location.title
        location.delete()
        messages.success(request, f'Маркер "{location_title}" успешно удален!')
        return redirect('home')

    return render(request, 'maps/confirm_delete.html', {'location': location})


def add_request(request):
    existing = DistributionRequest.objects.filter(
        user=request.user,
        status__in=['pending', 'in_work']
    ).first()

    if existing:
        messages.warning(request, f'У вас уже есть активная заявка #{existing.id}')
        return redirect('my_requests')

    if request.method == 'POST':
        form = DistributionRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, f'Заявка #{req.id} успешно отправлена!')
            return redirect('home')
    else:
        initial = {}

        if 'lat' in request.GET and 'lon' in request.GET:
            initial['latitude'] = float(request.GET.get('lat'))
            initial['longitude'] = float(request.GET.get('lon'))

        if 'demo' in request.GET and request.GET.get('demo') == '1':
            initial['company_name'] = 'ООО Тестовая компания'
            initial['business_type'] = 'services'
            initial['description'] = 'Тестовое описание деятельности компании'
            initial['contact_person'] = 'Иван Иванов'
            initial['phone'] = '+7 (999) 123-45-67'
            initial['email'] = 'test@example.com'
            initial['address'] = 'г. Москва, ул. Тестовая, д. 1'
            initial['city'] = 'Москва'
            initial['employees_count'] = 10
            initial['need_1c_buh'] = True
            initial['need_1c_trade'] = True
            initial['comment'] = 'Тестовая заявка для демонстрации'

        form = DistributionRequestForm(initial=initial)

    return render(request, 'maps/add_request.html', {'form': form})

@login_required
def my_requests(request):
    """Список моих заявок"""
    requests = DistributionRequest.objects.filter(user=request.user)
    return render(request, 'maps/my_requests.html', {'requests': requests})


@login_required
def request_detail(request, pk):
    """Детальная информация о заявке"""
    req = get_object_or_404(DistributionRequest, pk=pk, user=request.user)
    return render(request, 'maps/request_detail.html', {'request': req})


@login_required
def cancel_request(request, pk):
    """Отмена заявки"""
    req = get_object_or_404(DistributionRequest, pk=pk, user=request.user)

    if req.status not in ['pending', 'in_work']:
        messages.error(request, 'Нельзя отменить обработанную заявку')
        return redirect('my_requests')

    if request.method == 'POST':
        req.status = 'rejected'
        req.save()
        messages.success(request, f'Заявка #{req.id} отменена')
        return redirect('my_requests')

    return render(request, 'maps/cancel_request.html', {'request': req})