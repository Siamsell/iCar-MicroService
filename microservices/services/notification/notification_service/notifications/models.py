from django.db import models
from django.utils import timezone
from datetime import timedelta

        
class UserModel(models.Model):
    
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=10, default='user')
    date_joined = models.DateTimeField()
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def is_admin(self):
        return self.role == 'admin'

class VehiculeModel(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.id}"
    
    class Meta:
        ordering = ['id']

class Notification(models.Model):
    class Type(models.TextChoices):
        FOLLOW_USER = "follow_user", "Follow User"
        FOLLOW_POST = "follow_post", "Follow Post"
        POST = "post", "Post"
    
    user       = models.ForeignKey(UserModel, on_delete=models.CASCADE,related_name="notifications")        
    subject    = models.CharField(max_length=255)
    message    = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    post       = models.ForeignKey(VehiculeModel, on_delete=models.CASCADE, null=True, blank=True)
    follower = models.ForeignKey(UserModel, on_delete=models.CASCADE, null=True, blank=True,related_name="sent_notifications")
    type = models.CharField(max_length=20, choices=Type.choices)

    class Meta:
        ordering = ['-created_at']
        unique_together = [
            ['user', 'follower', 'type'],  
            ['user', 'post', 'type'],         
        ]

    def __str__(self):
        return f"Notification({self.id}) → user {self.user}: {self.subject}"


class UserFollowPost(models.Model):
    """
    Tracks which users are following which posts.
    Used by the worker to fan-out notifications when a post changes.
    """
    user   = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    post    = models.ForeignKey(VehiculeModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'post'],
                name='unique_user_post_follow'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"User {self.user} follows post {self.post}"


class UserFollowUser(models.Model):
    """
    Tracks which users are following which other users.
    Used by the worker to fan-out notifications when a user publishes content.
    """
    follower  = models.ForeignKey(UserModel, on_delete=models.CASCADE,related_name="following")
    following = models.ForeignKey(UserModel, on_delete=models.CASCADE,related_name="followers")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_user_follow'
            ),
            models.CheckConstraint(
    condition=~models.Q(follower=models.F('following')),
    name='prevent_self_follow_user'
)
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"User {self.follower} follows user {self.following}"
