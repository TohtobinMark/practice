from django.test import TestCase
from django.contrib.auth.models import User
from .models import Location, DistributionRequest


class LocationModelTest(TestCase):
    def test_location_creation(self):
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        location = Location.objects.create(
            user=user,
            title='ООО Ромашка',
            description='Розничная торговля',
            latitude=55.755826,
            longitude=37.617300
        )
        self.assertEqual(location.title, 'ООО Ромашка')
        self.assertEqual(location.latitude, 55.755826)
        self.assertEqual(location.longitude, 37.617300)
        self.assertEqual(str(location), 'ООО Ромашка')
        self.assertIsNotNone(location.created_at)


class DistributionRequestTest(TestCase):
    def test_request_creation(self):
        user = User.objects.create_user(
            username='clientuser',
            password='clientpass123'
        )
        request = DistributionRequest.objects.create(
            user=user,
            company_name='ООО Тест',
            business_type='retail',
            contact_person='Марк Алихан',
            phone='+7 (999) 123-45-67',
            email='alixan@test.ru',
            latitude=55.755826,
            longitude=37.617300,
            address='г. Абакан',
            city='Абакан',
            employees_count=10,
            need_1c_buh=True,
            status='pending'
        )
        self.assertEqual(request.company_name, 'ООО Тест')
        self.assertEqual(request.contact_person, 'Марк Алихан')
        self.assertEqual(request.status, 'pending')
        self.assertTrue(request.need_1c_buh)
        self.assertEqual(str(request), f'Заявка #{request.id} - ООО Тест')


class UserRelationTest(TestCase):
    def test_user_relations(self):
        # Создаем пользователя
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        Location.objects.create(
            user=user,
            title='Клиент 1',
            latitude=55.755826,
            longitude=37.617300
        )
        DistributionRequest.objects.create(
            user=user,
            company_name='Заявка 1',
            contact_person='Иван',
            phone='+7 (999) 111-22-33',
            email='test@test.ru',
            latitude=55.755826,
            longitude=37.617300,
            address='Москва',
            city='Москва'
        )
        self.assertEqual(user.locations.count(), 1)
        self.assertEqual(user.locations.first().title, 'Клиент 1')
        self.assertEqual(user.distribution_requests.count(), 1)
        self.assertEqual(user.distribution_requests.first().company_name,
                         'Заявка 1')
        user.delete()
        self.assertEqual(Location.objects.count(), 0)
        self.assertEqual(DistributionRequest.objects.count(), 0)