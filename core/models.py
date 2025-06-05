# core/models.py
from django.db import models
from django.contrib.auth.models import User #Importo o User padrão do Django para o Medico
from django.utils import timezone #Para usar como default em campos de data/hora
from django.db.models import JSONField #Para armazenar listas/dicionários de forma flexível (ex: exames)

#Modelo Paciente: aqui guardo todas as informações do paciente.
#Tanto dados cadastrais básicos quanto informações clínicas que podem ser preenchidas
#pelo médico durante o atendimento.
class Paciente(models.Model):
    # Dados Cadastrais Básicos
    nome_completo = models.CharField(max_length=255, verbose_name='Nome Completo') # Nome completo do paciente
    data_nascimento = models.DateField(verbose_name='Data de Nascimento') # Data de nascimento
    idade = models.IntegerField(blank=True, null=True, verbose_name='Idade') # Idade, pode ser calculada ou preenchida. blank/null=True porque pode ser opcional ou calculada depois.
    nome_mae = models.CharField(max_length=255, verbose_name='Nome da Mãe') # Nome da mãe, importante para identificação
    carteira_sus = models.CharField(max_length=20, unique=True, verbose_name='Carteira do SUS') # Número do SUS, deve ser único
    plano_saude = models.CharField(max_length=100, blank=True, null=True, verbose_name='Plano de Saúde') # Plano de saúde, se tiver (opcional)

    # Informações Clínicas - geralmente preenchidas pelo médico
    # Todas são blank=True e null=True porque podem não ser preenchidas inicialmente ou em todos os atendimentos.
    queixa_principal = models.TextField(blank=True, null=True, verbose_name='Queixa Principal') # O motivo principal da consulta
    inicio_doenca = models.TextField(blank=True, null=True, verbose_name='Quando a doença começou') # Descrição de quando os sintomas iniciaram
    localizacao_dor = models.CharField(max_length=255, blank=True, null=True, verbose_name='Localização da Dor') # Onde dói
    caracteristicas_dor = models.TextField(blank=True, null=True, verbose_name='Características da Dor') # Como é a dor (pontada, queimação, etc.)
    evolucao_quadro = models.TextField(blank=True, null=True, verbose_name='Evolução do quadro') # Como o quadro clínico tem evoluído
    alergias = models.TextField(blank=True, null=True, verbose_name='Alergias') # Lista de alergias conhecidas
    doencas_pre_existentes = models.TextField(blank=True, null=True, verbose_name='Doenças Pre-existentes') # Outras doenças que o paciente já possui

    # Representação em string do objeto Paciente. Facilita na visualização no admin e em debugs.
    def __str__(self):
        return self.nome_completo

# Modelo Medico: representa o profissional de saúde.
# Está ligado ao User do Django para autenticação e permissões.
class Medico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Relacionamento um-para-um com o User. Se o User for deletado, o Medico também é.
    especialidade = models.CharField(max_length=100, verbose_name='Especialidade') # Ex: Cardiologia, Clínica Geral
    crm = models.CharField(max_length=20, unique=True, verbose_name='CRM') # CRM do médico, deve ser único
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefone') # Contato telefônico (opcional)
    email = models.EmailField(blank=True, null=True, verbose_name='Email') # Contato por email (opcional)

    # Representação em string do objeto Medico.
    # Tenta pegar o nome completo do User, se não tiver, usa o username.
    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.especialidade})'


# Modelo FilaAtendimento: é o coração do sistema de filas.
# Cada entrada representa um paciente em um determinado estado na fila para um médico.
class FilaAtendimento(models.Model):
    # Choices para o campo status. Facilita a padronização e a interface.
    STATUS_FILA = [
        ('AGUARDANDO', 'Aguardando'),         # Paciente chegou e está na fila.
        ('EM_ATENDIMENTO', 'Em Atendimento'), # Paciente foi chamado e está sendo atendido.
        ('ATENDIDO', 'Atendido'),             # Atendimento finalizado.
        ('CANCELADO', 'Cancelado'),           # Atendimento foi cancelado (pelo paciente ou sistema).
    ]

    # Relacionamentos e dados básicos da fila
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, verbose_name='Paciente') # Qual paciente está na fila. Se o paciente for deletado, a entrada na fila também é.
    medico_destino = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Médico de Destino') # Para qual médico o paciente foi encaminhado. SET_NULL para não perder o histórico da fila se o médico for deletado.
    status = models.CharField(max_length=20, choices=STATUS_FILA, default='AGUARDANDO', verbose_name='Status') # Status atual do paciente na fila.
    data_hora_chegada = models.DateTimeField(default=timezone.now, verbose_name='Hora da Chegada') # Quando o paciente entrou na fila. Default para o momento da criação.
    data_hora_chamada = models.DateTimeField(null=True, blank=True, verbose_name='Hora da Chamada') # Quando o paciente foi chamado para atendimento (opcional).
    data_hora_fim = models.DateTimeField(null=True, blank=True, verbose_name='Hora do Fim') # Quando o atendimento foi finalizado (opcional).
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações (Atendente)') # Observações adicionadas pelo atendente ao colocar na fila.

    # Campos para dados do atendimento (preenchidos pelo médico)
    # Usar JSONField aqui é uma boa porque a lista de exames pode variar muito, e não quero criar uma tabela separada só para isso
    # se a estrutura for simples (apenas uma lista de strings).
    exames_checkbox_selecionados = JSONField(null=True, blank=True, verbose_name="Exames Selecionados (Checkboxes)") # Armazena uma lista dos exames selecionados de uma lista pré-definida.
    exame_outro_digitado = models.TextField(null=True, blank=True, verbose_name="Outro Exame (Digitado)") # Caso o médico queira adicionar um exame que não está na lista.

    evolucao_consulta = models.TextField(blank=True, null=True, verbose_name="Evolução da Consulta") # Notas do médico sobre a evolução do paciente durante a consulta.
    conduta_adotada = models.TextField(blank=True, null=True, verbose_name="Conduta Adotada") # O que o médico decidiu fazer (receitas, encaminhamentos, etc.).

    # Meta informações do modelo.
    class Meta:
        verbose_name = 'Entrada na Fila' # Nome amigável para um único objeto no admin.
        verbose_name_plural = 'Fila de Atendimento' # Nome amigável para múltiplos objetos no admin.
        ordering = ['data_hora_chegada'] # Por padrão, ordenar as entradas na fila pela hora de chegada.

    # Representação em string do objeto FilaAtendimento.
    def __str__(self):
        return f"{self.paciente.nome_completo} - {self.get_status_display()} ({self.data_hora_chegada.strftime('%d/%m %H:%M')})"
        # Usei get_status_display() para pegar o valor "human-readable" do status.