#importando tudo 
from django.urls import path
from .views import (
    HomeView, 
    AtendentePainelView, PacienteCreateView, ChamarPacienteView, AtendimentoDetailView,
    FinalizarAtendimentoView, PacienteListView, AdicionarPacienteFilaView, PacienteUpdateView,
    PacienteClinicalUpdateView, PacienteDeleteView, MedicoPollingAPIView
)

# Importando as views necessárias para as URLs
urlpatterns = [
    path('', HomeView.as_view(), name='home'), 
    path('painel-atendente/', AtendentePainelView.as_view(), name='painel_atendente'),
    path('paciente/novo/', PacienteCreateView.as_view(), name='paciente_novo'),
    path('fila/chamar/<int:pk>/', ChamarPacienteView.as_view(), name='chamar_paciente'),
    path('atendimento/<int:pk>/', AtendimentoDetailView.as_view(), name='atendimento_detalhe'), 
    path('atendimento/finalizar/<int:pk>/', FinalizarAtendimentoView.as_view(), name='finalizar_atendimento'),
    path('pacientes/', PacienteListView.as_view(), name='paciente_list'),
    path('paciente/<int:paciente_pk>/adicionar-fila/', AdicionarPacienteFilaView.as_view(), name='adicionar_paciente_fila'),
    path('paciente/<int:pk>/editar/', PacienteUpdateView.as_view(), name='paciente_editar'),
    path('paciente/<int:pk>/atendimento/<int:atendimento_pk>/editar-clinico/', 
        PacienteClinicalUpdateView.as_view(), 
        name='paciente_editar_clinico'),
    path('paciente/<int:pk>/deletar/', PacienteDeleteView.as_view(), name='paciente_deletar'),
    path('api/medico/status-fila/', MedicoPollingAPIView.as_view(), name='api_medico_status_fila'),
]

print("Arquivo core/urls.py criado!")