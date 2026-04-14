import json
from django.db.models import Count
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Location, DistributionRequest, Service, ServiceCategory, License, User
from .forms import LocationForm, DistributionRequestForm, CustomUserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
import logging
from django.db import DatabaseError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
logger = logging.getLogger(__name__)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def home(request):
    try:
        try:
            clients = Location.objects.all()
        except DatabaseError as e:
            logger.error(f"Ошибка БД при получении клиентов: {e}")
            clients = []
            messages.error(request, 'Ошибка загрузки данных клиентов. Пожалуйста, обновите страницу.')

        try:
            requests = DistributionRequest.objects.exclude(status__in=['completed', 'rejected'])
        except DatabaseError as e:
            logger.error(f"Ошибка БД при получении заявок: {e}")
            requests = []
            messages.error(request, 'Ошибка загрузки данных заявок.')

        user_request = None
        if request.user.is_authenticated:
            try:
                user_request = DistributionRequest.objects.filter(
                    user=request.user
                ).exclude(status__in=['completed', 'rejected']).first()
            except (DatabaseError, ObjectDoesNotExist) as e:
                logger.error(f"Ошибка при получении заявки пользователя {request.user.id}: {e}")
                user_request = None

        # Получение сервисов и лицензий
        try:
            service_categories = ServiceCategory.objects.all().prefetch_related('service_set')
            services = Service.objects.all()
            licenses = License.objects.all()
        except DatabaseError as e:
            logger.error(f"Ошибка БД при получении сервисов/лицензий: {e}")
            service_categories = []
            services = []
            licenses = []

        search = request.GET.get('search', '')
        category_filter = request.GET.get('category_filter', '')
        sort_price = request.GET.get('sort_price', '')

        services_list = list(services)
        licenses_list = list(licenses)

        for service in services_list:
            service.item_type = 'service'
            service.category_name = service.category.name if service.category else 'Без категории'
            service.category_id = service.category.id if service.category else None

        for license_item in licenses_list:
            license_item.item_type = 'license'
            license_item.category_name = None
            license_item.category_id = None

        all_items = services_list + licenses_list

        if search:
            all_items = [
                item for item in all_items
                if search.lower() in item.name.lower()
                   or search.lower() in item.description.lower()
            ]

        if category_filter and category_filter.isdigit():
            all_items = [
                item for item in all_items
                if item.item_type == 'service' and item.category_id == int(category_filter)
            ]

        if sort_price == 'price_asc':
            all_items.sort(key=lambda x: float(x.price))
        elif sort_price == 'price_desc':
            all_items.sort(key=lambda x: float(x.price), reverse=True)

        if request.headers.get('HX-Request'):
            # Возвращаем ТОЛЬКО блок с продуктами, без всей страницы
            return render(request, 'maps/products_list.html', {
                'all_items': all_items,
                'items_has_licenses': any(item.item_type == 'license' for item in all_items),
                'items_has_services': any(item.item_type == 'service' for item in all_items),
                'search': search,
                'category_filter': category_filter,
                'sort_price': sort_price,
                'service_categories': service_categories,
            })

        context = {
            'clients': clients,
            'requests': requests,
            'user_request': user_request,
            'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
            'all_items': all_items,
            'items_has_licenses': any(item.item_type == 'license' for item in all_items),
            'items_has_services': any(item.item_type == 'service' for item in all_items),
            'service_categories': service_categories,
            'search': search,
            'category_filter': category_filter,
            'sort_price': sort_price,
            'services': services,
            'licenses': licenses,
        }

        return render(request, 'maps/home.html', context)

    except Exception as e:
        logger.error(f"Необработанная ошибка в home: {e}")
        messages.error(request, 'Произошла ошибка при загрузке страницы.')
        return render(request, 'maps/home.html', {'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', '')})

    except Exception as e:
        logger.critical(f"Критическая ошибка в home view: {e}")
        messages.error(request, 'Произошла ошибка при загрузке страницы. Попробуйте позже.')
        return render(request, 'maps/home.html', {
            'clients': [],
            'requests': [],
            'user_request': None,
            'services': [],
            'service_categories': [],
            'licenses': [],
            'error_occurred': True
        })


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

@login_required
def add_request(request):
    if request.user.role == 'guest':
        messages.error(request, 'Гостям недоступно создание заявок. Пожалуйста, зарегистрируйтесь.')
        return redirect('login')
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
            messages.success(request, f'Заявка успешно отправлена!')
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
    if request.user.role == 'guest':
        return redirect('login')
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


@staff_member_required
def admin_statistics(request):
    """Страница статистики для администратора"""

    # Общая статистика
    total_users = User.objects.count()
    total_clients = Location.objects.count()
    total_requests = DistributionRequest.objects.count()

    # Статистика по статусам
    pending_requests = DistributionRequest.objects.filter(status='pending').count()
    in_work_requests = DistributionRequest.objects.filter(status='in_work').count()
    completed_requests = DistributionRequest.objects.filter(status='completed').count()
    rejected_requests = DistributionRequest.objects.filter(status='rejected').count()

    # Статистика по типам бизнеса
    business_types = DistributionRequest.objects.values('business_type').annotate(
        count=Count('id')
    )
    business_types_dict = {}
    for item in business_types:
        business_types_dict[
            dict(DistributionRequest.BUSINESS_TYPES).get(item['business_type'], item['business_type'])] = item['count']

    context = {
        'total_users': total_users,
        'total_clients': total_clients,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'in_work_requests': in_work_requests,
        'completed_requests': completed_requests,
        'rejected_requests': rejected_requests,
        'business_types': business_types_dict,
    }
    return render(request, 'admin/admin_statistics.html', context)


@staff_member_required
def admin_requests(request):
    """Страница для администратора со всеми заявками"""
    from django.utils import timezone
    requests = DistributionRequest.objects.all().order_by('-created_at')

    context = {
        'requests': requests,
        'now': timezone.now(),
    }
    return render(request, 'admin/admin_requests.html', context)

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        messages.success(self.request, f'Добро пожаловать, {user.username}! Вы успешно вошли в систему.')
        return response


class CustomLogoutView(LogoutView):
    next_page = 'login'
    def dispatch(self, request, *args, **kwargs):
        username = request.user.username if request.user.is_authenticated else 'Пользователь'
        response = super().dispatch(request, *args, **kwargs)
        messages.info(request, f'{username}, вы успешно вышли из системы. До новых встреч!')
        return response


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')

    return render(request, 'registration/login.html')


def custom_logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'{username}, вы успешно вышли из системы.')
    return redirect('login')

@login_required
def add_service(request):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    if request.method == 'POST':
        try:
            service = Service()
            service.name = request.POST.get('name')
            service.description = request.POST.get('description', '')
            service.price = request.POST.get('price', 0)
            service.discount = request.POST.get('discount', 0)
            service.category_id = request.POST.get('category_id')

            if request.FILES.get('image'):
                service.image = request.FILES['image']

            service.save()
            messages.success(request, 'Сервис успешно добавлен')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении сервиса: {e}')

    return redirect('home')


@login_required
def add_license(request):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    if request.method == 'POST':
        try:
            license_item = License()
            license_item.name = request.POST.get('name')
            license_item.description = request.POST.get('description', '')
            license_item.price = request.POST.get('price', 0)
            license_item.discount = request.POST.get('discount', 0)

            if request.FILES.get('image'):
                license_item.image = request.FILES['image']

            license_item.save()
            messages.success(request, 'Лицензия успешно добавлена')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении лицензии: {e}')

    return redirect('home')


@login_required
def edit_service(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        try:
            service.name = request.POST.get('name')
            service.description = request.POST.get('description', '')
            service.price = request.POST.get('price', 0)
            service.discount = request.POST.get('discount', 0)
            service.category_id = request.POST.get('category_id')

            if request.POST.get('delete_image'):
                service.image.delete()
                service.image = None
            elif request.FILES.get('image'):
                if service.image:
                    service.image.delete()
                service.image = request.FILES['image']

            service.save()
            messages.success(request, 'Сервис успешно обновлен')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении сервиса: {e}')

    return redirect('home')


@login_required
def edit_license(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    license_item = get_object_or_404(License, pk=pk)

    if request.method == 'POST':
        try:
            license_item.name = request.POST.get('name')
            license_item.description = request.POST.get('description', '')
            license_item.price = request.POST.get('price', 0)
            license_item.discount = request.POST.get('discount', 0)

            if request.POST.get('delete_image'):
                license_item.image.delete()
                license_item.image = None
            elif request.FILES.get('image'):
                if license_item.image:
                    license_item.image.delete()
                license_item.image = request.FILES['image']

            license_item.save()
            messages.success(request, 'Лицензия успешно обновлена')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении лицензии: {e}')

    return redirect('home')


@login_required
def delete_service(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    if request.method == 'POST':
        try:
            service = get_object_or_404(Service, pk=pk)
            if service.image:
                service.image.delete()
            service.delete()
            messages.success(request, 'Сервис успешно удален')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении сервиса: {e}')

    return redirect('home')


@login_required
def delete_license(request, pk):
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен')
        return redirect('home')

    if request.method == 'POST':
        try:
            license_item = get_object_or_404(License, pk=pk)
            if license_item.image:
                license_item.image.delete()
            license_item.delete()
            messages.success(request, 'Лицензия успешно удалена')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении лицензии: {e}')

    return redirect('home')

def is_superuser(user):
    return user.is_superuser

# Мягкое удаление (для всех сотрудников)
@staff_member_required
def soft_delete_license(request, pk):
    license = get_object_or_404(License, pk=pk)  # objects уже фильтрует
    license.soft_delete()
    messages.success(request, f'Лицензия "{license.name}" перемещена в корзину')
    return redirect('home')

@staff_member_required
def soft_delete_service(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.soft_delete()
    messages.success(request, f'Сервис "{service.name}" перемещен в корзину')
    return redirect('home')

# Восстановление (для сотрудников)
@staff_member_required
def restore_license(request, pk):
    license = License.all_objects.get(pk=pk)  # Используем all_objects для поиска удаленных
    license.restore()
    messages.success(request, f'Лицензия "{license.name}" восстановлена')
    return redirect('deleted_items')

@staff_member_required
def restore_service(request, pk):
    service = Service.all_objects.get(pk=pk)
    service.restore()
    messages.success(request, f'Сервис "{service.name}" восстановлен')
    return redirect('deleted_items')

# Жесткое удаление (только для суперпользователя)
@user_passes_test(is_superuser)
def hard_delete_license(request, pk):
    license = License.all_objects.get(pk=pk)
    license.delete()
    messages.success(request, 'Лицензия полностью удалена')
    return redirect('deleted_items')

@user_passes_test(is_superuser)
def hard_delete_service(request, pk):
    service = Service.all_objects.get(pk=pk)
    service.delete()
    messages.success(request, 'Сервис полностью удален')
    return redirect('deleted_items')


@staff_member_required
def deleted_items(request):
    # Получаем параметры
    type_filter = request.GET.get('type', '')
    sort = request.GET.get('sort', '-delete_date')

    # Получаем удаленные записи - используем all_objects
    deleted_licenses = License.all_objects.filter(delete_date__isnull=False)
    deleted_services = Service.all_objects.filter(delete_date__isnull=False)
    if sort == 'name':
        deleted_licenses = deleted_licenses.order_by('name')
        deleted_services = deleted_services.order_by('name')
    elif sort == '-name':
        deleted_licenses = deleted_licenses.order_by('-name')
        deleted_services = deleted_services.order_by('-name')
    elif sort == 'price':
        deleted_licenses = deleted_licenses.order_by('price')
        deleted_services = deleted_services.order_by('price')
    elif sort == '-price':
        deleted_licenses = deleted_licenses.order_by('-price')
        deleted_services = deleted_services.order_by('-price')
    elif sort == 'delete_date':
        deleted_licenses = deleted_licenses.order_by('delete_date')
        deleted_services = deleted_services.order_by('delete_date')
    else:  # -delete_date
        deleted_licenses = deleted_licenses.order_by('-delete_date')
        deleted_services = deleted_services.order_by('-delete_date')

    # Фильтрация по типу для all_items
    if type_filter == 'license':
        all_items = list(deleted_licenses)
    elif type_filter == 'service':
        all_items = list(deleted_services)
    else:
        # Объединяем списки
        all_items = list(deleted_licenses) + list(deleted_services)

    context = {
        'all_items': all_items,
        'deleted_licenses': deleted_licenses,
        'deleted_services': deleted_services,
    }

    # Если HTMX запрос, возвращаем только контент
    if request.headers.get('HX-Request'):
        return render(request, 'maps/deleted_items_content.html', context)

    return render(request, 'maps/deleted_items.html', context)