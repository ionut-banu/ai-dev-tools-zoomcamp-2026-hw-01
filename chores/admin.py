from django.contrib import admin

from chores.models import Chore, CompletionLog, HouseholdMember

admin.site.register(HouseholdMember)
admin.site.register(Chore)
admin.site.register(CompletionLog)
