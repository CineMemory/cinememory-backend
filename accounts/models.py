from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import os

# Create your models here.
def user_profile_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{instance.id}.{ext}'
    return os.path.join('profile_images', filename)

class User(AbstractUser):
    birth = models.DateField() 
    profile_image = models.ImageField(
        upload_to=user_profile_image_path,
        null=True,
        blank=True,
        default='profile_images/default.jpg'
    )

    def user_profile_image_path(instance, filename):
        ext = filename.split('.')[-1]
        filename = f'{instance.id}.{ext}'
        return os.path.join('profile_images', filename)
    
    
    @property
    def profile_image_url(self):
        if self.profile_image:
            return self.profile_image.url
        else:
            return '/media/default.jpg'