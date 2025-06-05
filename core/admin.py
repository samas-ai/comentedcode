# core/admin.py
from django.contrib import admin
from .models import Paciente, Medico, FilaAtendimento
from .models import Paciente, Medico # Importa seus modelos
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


admin.site.register(Paciente)

class MedicoInline(admin.StackedInline):
    model = Medico
    can_delete = False
    verbose_name_plural = 'Perfil Médico'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    inlines = (MedicoInline,) 

admin.site.unregister(User) 
admin.site.register(User, UserAdmin) 

@admin.register(FilaAtendimento) 
class FilaAtendimentoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico_destino', 'status', 'data_hora_chegada')
    list_filter = ('status', 'medico_destino')
    search_fields = ('paciente__nome_completo',)

print("Modelos Paciente e Medico (integrado) registrados no Admin!")