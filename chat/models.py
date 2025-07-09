from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    bot_response = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.message}"


class UserTodo(models.Model):
    user = user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_description = models.CharField(max_length=255)
    suggested_by_curo = models.BooleanField(default=True) # Was this suggested by the AI?
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True) # For specific deadlines
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = " (Done)" if self.completed else ""
        return f"{self.user.username}: {self.task_description}{status}"

    class Meta:
        ordering = ['-created_at'] # Order by most recent first