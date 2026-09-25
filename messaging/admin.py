from django.contrib import admin
from .models import Conversation, Message, Call


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("patient", "provider", "appointment", "updated_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "content_preview", "created_at")
    list_filter = ("conversation",)

    def content_preview(self, obj):
        return (obj.content or "")[:50]
    content_preview.short_description = "Content"


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ("caller", "receiver", "call_type", "status", "started_at", "room_id")
    list_filter = ("call_type", "status", "started_at")
    search_fields = ("caller__username", "receiver__username", "room_id")
