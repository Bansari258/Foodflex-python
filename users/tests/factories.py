import factory
from django.contrib.auth.models import User
from users.models import Profile

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"bansarishah258+{n}@gmail.com")  # Use a sequence to avoid duplicates
    username = factory.LazyAttribute(lambda obj: obj.email)  # Ensure username matches email
    password = factory.PostGenerationMethodCall('set_password', 'B@ns@ri258')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    phone = factory.Faker('phone_number')

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Ensure the user doesn't already have a Profile
        user = kwargs['user']
        if hasattr(user, 'profile'):
            user.profile.delete()
        return super()._create(model_class, *args, **kwargs)