from django.contrib import admin # type: ignore
from django.contrib.auth.admin import UserAdmin # type: ignore
from .models import AIProduct, CommunityAnswer, CommunityQuestion, CustomUser, LawAuthority, StoreItem, SupportTicket, TransitorProfile, InstructorProfile, TaxWorkerProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'photo', 'is_staff', 'is_superuser')}
        ),
    )
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(TransitorProfile)
admin.site.register(InstructorProfile)
admin.site.register(TaxWorkerProfile)
admin.site.register(StoreItem)
admin.site.register(AIProduct)
admin.site.register(LawAuthority)
admin.site.register(CommunityQuestion)
admin.site.register(CommunityAnswer)
admin.site.register(SupportTicket)
 

