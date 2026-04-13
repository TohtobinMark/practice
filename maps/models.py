from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CHOICES = [
        ('guest', 'Гость'),
        ('user', 'Авторизованный пользователь'),
        ('admin', 'Администратор'),
    ]
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    company_name = models.CharField('Название компании', max_length=200, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_guest(self):
        return self.role == 'guest' or not self.is_authenticated

    def is_admin(self):
        return self.role == 'admin' or self.is_staff

class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    latitude = models.FloatField(verbose_name="Широта")
    longitude = models.FloatField(verbose_name="Долгота")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class DistributionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('in_work', 'В работе'),
        ('completed', 'Подключено'),
        ('rejected', 'Отказано'),
    ]

    BUSINESS_TYPES = [
        ('retail', 'Розничная торговля'),
        ('wholesale', 'Оптовая торговля'),
        ('manufacturing', 'Производство'),
        ('services', 'Услуги'),
        ('cafe', 'Кафе/Ресторан'),
        ('other', 'Другое'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='distribution_requests',
        verbose_name='Заявитель'
    )

    # Информация о предприятии
    company_name = models.CharField('Название предприятия', max_length=200)
    business_type = models.CharField('Сфера деятельности', max_length=50, choices=BUSINESS_TYPES)
    description = models.TextField('Описание деятельности', blank=True)

    # Контактные данные
    contact_person = models.CharField('Контактное лицо', max_length=100)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email')

    # Геоданные (где находится предприятие)
    latitude = models.FloatField('Широта')
    longitude = models.FloatField('Долгота')
    address = models.CharField('Адрес', max_length=300)
    city = models.CharField('Город', max_length=100)

    # Информация о потребностях
    employees_count = models.IntegerField('Количество сотрудников', default=1)
    need_1c_buh = models.BooleanField('Нужна 1С:Бухгалтерия', default=False)
    need_1c_trade = models.BooleanField('Нужна 1С:Управление торговлей', default=False)
    need_1c_salary = models.BooleanField('Нужна 1С:Зарплата и кадры', default=False)
    need_cloud = models.BooleanField('Интересует облачная версия', default=False)
    comment = models.TextField('Дополнительный комментарий', blank=True)

    # Статус заявки
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    manager_comment = models.TextField('Комментарий менеджера', blank=True)

    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField('Дата обработки', null=True, blank=True)

    class Meta:
        verbose_name = 'Заявка на дистрибутив'
        verbose_name_plural = 'Заявки на дистрибутив'
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id} - {self.company_name}"

    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'in_work': 'info',
            'completed': 'success',
            'rejected': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def get_status_display_ru(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=DistributionRequest)
def create_client_on_completed(sender, instance, **kwargs):
    """При изменении статуса заявки на 'completed' создаем клиента в Location"""
    if instance.status == 'completed':
        existing = Location.objects.filter(
            title=instance.company_name,
            latitude=instance.latitude,
            longitude=instance.longitude
        ).first()

        if not existing:
            Location.objects.create(
                user=instance.user,
                title=instance.company_name,
                description=f"Подключено по заявке #{instance.id}. Сфера: {instance.get_business_type_display()}",
                latitude=instance.latitude,
                longitude=instance.longitude
            )
            print(f"✅ Создан клиент {instance.company_name} из заявки #{instance.id}")

class ServiceCategory(models.Model):
    name = models.CharField(max_length=200)

class SoftDeleteManager(models.Manager):
    """Менеджер, который не показывает мягко удаленные записи"""
    def get_queryset(self):
        return super().get_queryset().filter(delete_date__isnull=True)

class AllObjectsManager(models.Manager):
    """Менеджер, который показывает ВСЕ записи (включая удаленные)"""
    def get_queryset(self):
        return super().get_queryset()

class Service(models.Model):
    """Сервисы 1С"""
    name = models.CharField('Название сервиса', max_length=200)
    description = models.TextField('Описание сервиса')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=0)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, null=True)
    image = models.ImageField('Изображение', blank=True, null=True)
    discount = models.IntegerField()
    delete_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Дата удаления")
    objects = SoftDeleteManager()  # По умолчанию - скрываем удаленные
    all_objects = AllObjectsManager()
    def soft_delete(self):
        self.delete_date = timezone.now()
        self.save()

    def restore(self):
        self.delete_date = None
        self.save()

    @property
    def is_deleted(self):
        return self.delete_date is not None

    def calculate_price_with_discount(self, price):
        if self.discount <= 0:
            return price
        discount_amount = price * self.discount / 100
        return price - discount_amount

    def get_price_display(self):
        """Форматированное отображение цены"""
        if self.price == 0:
            return 'Бесплатно'
        return f"{int(self.price)} ₽"

class License(models.Model):
    """Лицензии на программы 1С"""
    # Основная информация
    name = models.CharField('Название программы', max_length=200)
    description = models.TextField('Описание программы', max_length=200)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, default=0)
    discount = models.IntegerField()
    image = models.ImageField('Изображение', blank=True, null=True)
    delete_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name="Дата удаления")
    objects = SoftDeleteManager()  # По умолчанию - скрываем удаленные
    all_objects = AllObjectsManager()
    def soft_delete(self):
        self.delete_date = timezone.now()
        self.save()

    def restore(self):
        self.delete_date = None
        self.save()

    @property
    def is_deleted(self):
        return self.delete_date is not None

    def calculate_price_with_discount(self, price):
        if self.discount <= 0:
            return price
        discount_amount = price * self.discount / 100
        return price - discount_amount

    def get_price_display(self):
        """Форматированное отображение цены"""
        if self.price == 0:
            return 'Бесплатно'
        return f"{int(self.price)} ₽"