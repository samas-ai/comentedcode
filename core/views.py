# core/views.py
from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView # Esqueçi de remover essa linha duplicada, já que CreateView está abaixo
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # Mixins para controle de acesso
from .models import FilaAtendimento, Medico, Paciente # Nossos modelos
from django.urls import reverse_lazy # Para URLs reversas
from django.shortcuts import get_object_or_404, redirect # Atalhos úteis
from django.utils import timezone # Para lidar com data/hora
from django.contrib import messages # Para exibir mensagens ao usuário
from django.db.models import Q # Para queries complexas (OR, AND)
from django.views.generic.edit import CreateView, UpdateView, DeleteView # Views genéricas para CRUD
from django.contrib.messages.views import SuccessMessageMixin # Para adicionar mensagens de sucesso automaticamente
from django.http import JsonResponse # Para retornar respostas JSON (usado na API de polling)

# View para o médico verificar via AJAX se há pacientes na fila ou em atendimento.
# Isso é para atualizar a interface do médico dinamicamente sem recarregar a página.
class MedicoPollingAPIView(LoginRequiredMixin, UserPassesTestMixin, View):

    # test_func para UserPassesTestMixin: só permite acesso se o usuário pertencer ao grupo 'Médicos'.
    def test_func(self):
        return self.request.user.groups.filter(name='Médicos').exists()

    # Método GET, pois é uma consulta de dados.
    def get(self, request, *args, **kwargs):
        try:
            # Pego o objeto 'Medico' associado ao usuário logado.
            # Isso assume que temos um campo relacionado 'medico' no nosso User model ou um Profile.
            medico_logado = request.user.medico

            # Primeiro, verifico se há algum paciente JÁ EM ATENDIMENTO com este médico.
            atendimento_atual = FilaAtendimento.objects.filter(
                medico_destino=medico_logado,
                status='EM_ATENDIMENTO'
            ).order_by('-data_hora_chamada').first() # Pego o mais recente chamado, caso haja mais de um (não deveria).

            if atendimento_atual:
                # Se tem alguém em atendimento, retorno os dados desse atendimento.
                data = {
                    'status_geral': 'em_atendimento',
                    'atendimento_id': atendimento_atual.pk,
                    'paciente_id': atendimento_atual.paciente.pk,
                    'paciente_nome': atendimento_atual.paciente.nome_completo,
                    'status_atendimento': atendimento_atual.get_status_display(), # Pega o valor "human-readable" do status
                    'hora_chamada': atendimento_atual.data_hora_chamada.strftime('%H:%M') if atendimento_atual.data_hora_chamada else None,
                }
                return JsonResponse(data)

            # Se não há ninguém EM_ATENDIMENTO, procuro o próximo AGUARDANDO.
            proximo_aguardando = FilaAtendimento.objects.filter(
                medico_destino=medico_logado,
                status='AGUARDANDO'
            ).order_by('data_hora_chegada').first() # Pego o que chegou primeiro.

            if proximo_aguardando:
                # Se tem alguém aguardando, retorno os dados desse próximo paciente.
                data = {
                    'status_geral': 'aguardando_proximo',
                    'atendimento_id': proximo_aguardando.pk,
                    'paciente_id': proximo_aguardando.paciente.pk,
                    'paciente_nome': proximo_aguardando.paciente.nome_completo,
                    'status_atendimento': proximo_aguardando.get_status_display(),
                    'hora_chegada': proximo_aguardando.data_hora_chegada.strftime('%H:%M:%S'),
                }
                return JsonResponse(data)

            # Se não tem ninguém em atendimento nem aguardando.
            return JsonResponse({'status_geral': 'sem_pacientes_na_fila'})

        except Medico.DoesNotExist:
            # Caso o usuário logado não tenha um perfil de médico associado.
            return JsonResponse({'status_geral': 'erro', 'mensagem': 'Perfil de médico não encontrado.'}, status=403)
        except Exception as e:
            # Um log para mim, no servidor, para debugar caso algo dê errado.
            print(f"Erro na MedicoPollingAPIView: {e}")
            return JsonResponse({'status_geral': 'erro', 'mensagem': 'Ocorreu um erro no servidor.'}, status=500)

# View para deletar um Paciente.
# Usa SuccessMessageMixin para exibir uma mensagem de sucesso automaticamente.
class PacienteDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Paciente # Modelo que esta view vai manipular.
    template_name = 'paciente_confirm_delete.html' # Template de confirmação.
    success_url = reverse_lazy('paciente_list') # Para onde redirecionar após a exclusão bem-sucedida.

    # Só quem é do grupo 'Atendentes' pode deletar pacientes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Adiciono um título à página para clareza.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Confirmar Exclusão: {self.object.nome_completo}"
        return context

    # Sobrescrevo form_valid para adicionar uma mensagem de sucesso personalizada usando o messages framework.
    # O SuccessMessageMixin usaria o atributo `success_message`, mas aqui prefiro formatar dinamicamente.
    def form_valid(self, form):
        messages.success(self.request, f"Paciente {self.object.nome_completo} excluído com sucesso!")
        return super().form_valid(form)


# View para o Médico atualizar informações CLÍNICAS de um Paciente.
# Esta view é acessada geralmente a partir da tela de atendimento.
class PacienteClinicalUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Paciente
    template_name = 'paciente_clinical_form.html' # Um formulário específico para dados clínicos.
    fields = [ # Campos que o médico pode editar.
        'queixa_principal',
        'inicio_doenca',
        'localizacao_dor',
        'caracteristicas_dor',
        'evolucao_quadro',
        'alergias',
        'doencas_pre_existentes'
    ]

    # Só médicos podem acessar.
    def test_func(self):
        return self.request.user.groups.filter(name='Médicos').exists()

    # Após atualizar, quero voltar para a tela de detalhes do atendimento, se eu vim de lá.
    def get_success_url(self):
        atendimento_pk = self.kwargs.get('atendimento_pk') # Pego o pk do atendimento da URL.
        if atendimento_pk:
            return reverse_lazy('atendimento_detalhe', kwargs={'pk': atendimento_pk})
        return reverse_lazy('home') # Fallback, caso não tenha o pk do atendimento.

    # Contexto para o template.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f"Editando Informações Clínicas de: {self.object.nome_completo}"
        # Passo o pk do atendimento para o template, caso o usuário queira cancelar e voltar.
        context['atendimento_pk_para_cancelar'] = self.kwargs.get('atendimento_pk')
        return context

    # Mensagem de sucesso customizada para o SuccessMessageMixin.
    def get_success_message(self, cleaned_data):
        return f"Informações clínicas do paciente {self.object.nome_completo} atualizadas com sucesso!"


# View para o Atendente atualizar dados CADASTRAIS de um Paciente.
class PacienteUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Paciente
    template_name = 'paciente_form.html' # Um formulário genérico para dados do paciente.
    fields = [ # Campos que o atendente pode editar.
        'nome_completo', 'data_nascimento', 'idade', 'nome_mae', 'carteira_sus',
        'plano_saude',
    ]
    success_url = reverse_lazy('paciente_list') # Volta para a lista de pacientes.
    success_message = "Dados do paciente %(nome_completo)s atualizados com sucesso!" # Mensagem padrão do SuccessMessageMixin.

    # Só atendentes podem acessar.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Contexto para o template.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f"Editando Paciente: {self.object.nome_completo}"
        return context

# View para o Atendente adicionar um PACIENTE JÁ EXISTENTE à fila de um médico.
class AdicionarPacienteFilaView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = FilaAtendimento # Vamos criar uma nova entrada na FilaAtendimento.
    template_name = 'adicionar_paciente_fila_form.html'
    fields = ['medico_destino', 'observacoes'] # O atendente escolhe o médico e pode adicionar observações.

    # Só atendentes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Após adicionar à fila, volta para o painel do atendente.
    def get_success_url(self):
        return reverse_lazy('painel_atendente')

    # No contexto, preciso saber qual paciente estou adicionando à fila.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paciente_pk = self.kwargs.get('paciente_pk') # Pego o pk do paciente da URL.
        context['paciente_para_adicionar'] = get_object_or_404(Paciente, pk=paciente_pk)
        return context

    # Antes de salvar o formulário da FilaAtendimento, preciso associar o paciente.
    def form_valid(self, form):
        paciente_pk = self.kwargs.get('paciente_pk')
        paciente_obj = get_object_or_404(Paciente, pk=paciente_pk)

        form.instance.paciente = paciente_obj # Associo o paciente ao form.instance.
        form.instance.status = 'AGUARDANDO' # Status inicial.
        # data_hora_chegada é auto_now_add no model, então não preciso setar aqui.

        messages.success(self.request, f"Paciente {paciente_obj.nome_completo} adicionado à fila com sucesso!")
        return super().form_valid(form)

# View da página inicial (Home).
# Mostra informações diferentes dependendo do grupo do usuário (Atendente ou Médico).
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Verifico a quais grupos o usuário pertence.
        is_atendente = user.groups.filter(name='Atendentes').exists()
        is_medico = user.groups.filter(name='Médicos').exists()

        context['is_atendente'] = is_atendente
        context['is_medico'] = is_medico

        if is_atendente:
            # Mensagens específicas para Atendentes.
            context['mensagem_boas_vindas'] = f"Bem-vindo(a), {user.first_name or user.username}! Pronto(a) para organizar as filas?"
            context['sub_mensagem'] = "Use os botões abaixo para gerenciar os pacientes e o fluxo de atendimento."
        elif is_medico:
            # Mensagens e dados específicos para Médicos.
            context['mensagem_boas_vindas'] = f"Bem-vindo(a), Dr(a). {user.last_name or user.username}!"

            try:
                medico_logado = user.medico # Pego o objeto Medico.

                # Busco pacientes em atendimento por este médico.
                pacientes_em_atendimento = FilaAtendimento.objects.filter(
                    medico_destino=medico_logado,
                    status='EM_ATENDIMENTO'
                ).order_by('data_hora_chamada')

                # Busco pacientes aguardando por este médico.
                pacientes_aguardando = FilaAtendimento.objects.filter(
                    medico_destino=medico_logado,
                    status='AGUARDANDO'
                ).order_by('data_hora_chegada')

                context['pacientes_em_atendimento_count'] = pacientes_em_atendimento.count()
                context['pacientes_aguardando_count'] = pacientes_aguardando.count()

                proximo_atendimento_obj = None
                # Determino qual o "próximo" paciente (seja para continuar ou iniciar).
                if pacientes_em_atendimento.exists(): # Prioridade para quem já está em atendimento.
                    proximo_atendimento_obj = pacientes_em_atendimento.first()
                    context['acao_proximo_atendimento'] = "Continuar Atendimento"
                elif pacientes_aguardando.exists(): # Se não, pego o próximo da fila.
                    proximo_atendimento_obj = pacientes_aguardando.first()
                    context['acao_proximo_atendimento'] = "Iniciar Próximo Atendimento"

                context['proximo_atendimento_obj'] = proximo_atendimento_obj

            except Medico.DoesNotExist:
                # Caso o usuário médico não tenha perfil.
                context['pacientes_em_atendimento_count'] = 0
                context['pacientes_aguardando_count'] = 0
                context['proximo_atendimento_obj'] = None
                messages.warning(self.request, "Seu perfil de médico não foi encontrado. Por favor, contate o administrador.")

            context['sub_mensagem'] = "Aqui está um resumo da sua fila e acesso rápido."

        else:
            # Para outros tipos de usuários (ex: admin, se não for médico nem atendente).
            context['mensagem_boas_vindas'] = f"Bem-vindo(a), {user.username}!"
            context['sub_mensagem'] = "Você está logado no Gestor de Filas."

        return context

# Painel do Atendente: lista os pacientes que estão AGUARDANDO na fila.
# Permite filtrar por médico.
class AtendentePainelView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FilaAtendimento
    template_name = 'atendente_painel.html'
    context_object_name = 'fila_list' # Nome da variável no template para a lista de itens da fila.
    paginate_by = 5 # Quantos itens por página.

    # Só atendentes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Defino o queryset base e aplico filtros se necessário.
    def get_queryset(self):
        queryset = FilaAtendimento.objects.filter(status='AGUARDANDO') # Só os que estão aguardando.

        medico_id_da_url = self.request.GET.get('medico_id') # Pego o 'medico_id' da URL (query param).

        if medico_id_da_url: # Se foi passado um ID de médico para filtrar...
            try:
                medico_id_int = int(medico_id_da_url)
                queryset = queryset.filter(medico_destino_id=medico_id_int)
                # Esse print é para debug, para ver se o filtro está funcionando como esperado.
                print(f"DEBUG get_queryset: Filtrando por medico_id = {medico_id_int}")
            except ValueError:
                # Se o medico_id não for um número válido, ignoro o filtro.
                print(f"DEBUG get_queryset: medico_id '{medico_id_da_url}' inválido, não filtrando.")
                pass # Não faz nada, apenas usa o queryset original sem o filtro de médico.
        else:
            # Se nenhum medico_id foi passado, mostro a fila geral de todos os médicos.
            print("DEBUG get_queryset: Nenhum medico_id na URL, mostrando Fila Geral.")

        return queryset.order_by('data_hora_chegada') # Ordeno pela hora de chegada.

    # Adiciono mais coisas ao contexto.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medicos'] = Medico.objects.all() # Para popular um dropdown de filtro de médicos.

        medico_id_da_url = self.request.GET.get('medico_id')
        context['medico_selecionado'] = None # Inicializo como None.

        if medico_id_da_url:
            try:
                medico_id_int = int(medico_id_da_url)
                context['medico_selecionado'] = Medico.objects.get(pk=medico_id_int) # Para saber qual médico está selecionado.
                # Mais debug.
                print(f"DEBUG get_context_data: Médico Selecionado: {context['medico_selecionado']}")
            except Medico.DoesNotExist:
                print(f"DEBUG get_context_data: Médico com ID {medico_id_da_url} não encontrado.")
            except ValueError:
                print(f"DEBUG get_context_data: medico_id '{medico_id_da_url}' inválido.")
        else:
            print("DEBUG get_context_data: Nenhum medico_id na URL para medico_selecionado.")

        return context


# View para o Atendente cadastrar um NOVO Paciente.
# Pode, opcionalmente, já adicionar este novo paciente à fila de um médico específico.
class PacienteCreateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, CreateView):
    model = Paciente
    template_name = 'paciente_form.html' # Reutilizo o mesmo form de edição.
    fields = [
        'nome_completo', 'data_nascimento', 'idade', 'nome_mae', 'carteira_sus',
        'plano_saude'
    ]

    # Só atendentes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Defino um título para o formulário, que pode mudar se estivermos adicionando à fila de um médico.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medico_id_param = self.request.GET.get('medico_id') # Pego da URL.
        if medico_id_param:
            try:
                medico = Medico.objects.get(pk=medico_id_param)
                # Se tem medico_id, o título indica que vamos cadastrar E adicionar à fila.
                context['form_title'] = f"Cadastrar Paciente e Adicionar à Fila do(a) Dr(a). {medico.user.get_full_name() or medico.user.username}"
            except Medico.DoesNotExist:
                context['form_title'] = "Cadastrar Novo Paciente (Médico não encontrado)"
        else:
            # Título padrão.
            context['form_title'] = "Cadastrar Novo Paciente"
        return context

    # Lógica principal: salvar o paciente e, se houver medico_id, criar a entrada na fila.
    def form_valid(self, form):
        self.object = form.save() # Salvo o paciente primeiro.
        novo_paciente = self.object

        medico_id = self.request.GET.get('medico_id') # Pego o ID do médico da URL (se existir).

        if medico_id:
            try:
                medico_obj = Medico.objects.get(pk=medico_id)
                # Crio a entrada na FilaAtendimento para este novo paciente e o médico especificado.
                FilaAtendimento.objects.create(
                    paciente=novo_paciente,
                    medico_destino=medico_obj,
                    status='AGUARDANDO',
                    # data_hora_chegada é auto_now_add
                )
                messages.success(self.request, f"Paciente {novo_paciente.nome_completo} cadastrado e adicionado à fila do(a) Dr(a). {medico_obj.user.get_full_name() or medico_obj.user.username}.")
            except Medico.DoesNotExist:
                messages.warning(self.request, f"Paciente {novo_paciente.nome_completo} cadastrado, mas o médico (ID: {medico_id}) não foi encontrado. Paciente não adicionado à fila.")
            except Exception as e: # Captura outros erros na criação da FilaAtendimento.
                messages.error(self.request, f"Paciente {novo_paciente.nome_completo} cadastrado, mas ocorreu um erro ao adicioná-lo à fila. Detalhe: {e}")
        else:
            # Se não tinha medico_id, apenas informo que o paciente foi cadastrado.
            messages.info(self.request, f"Paciente {novo_paciente.nome_completo} cadastrado. Agora, atribua-o a uma fila.")

        # Chamo o super().form_valid() no final para garantir o fluxo padrão do CreateView,
        # incluindo o redirecionamento para get_success_url().
        # O SuccessMessageMixin, se `success_message` estivesse definido, atuaria aqui.
        # Como estou usando messages.xxx() manualmente, o `success_message` do mixin não será usado neste fluxo específico.
        return super().form_valid(form)


    # Define para onde ir após o cadastro.
    def get_success_url(self):
        medico_id_na_url_original = self.request.GET.get('medico_id')

        if medico_id_na_url_original:
            # Se cadastrou e já adicionou à fila (pois tinha medico_id), volta pro painel do atendente.
            return reverse_lazy('painel_atendente')
        else:
            # Se apenas cadastrou o paciente (sem medico_id), leva para a tela de adicionar à fila,
            # já com o paciente recém-criado selecionado.
            return reverse_lazy('adicionar_paciente_fila', kwargs={'paciente_pk': self.object.pk})


# View para o Atendente "chamar" um paciente da fila.
# Isso muda o status do paciente de 'AGUARDANDO' para 'EM_ATENDIMENTO'.
class ChamarPacienteView(LoginRequiredMixin, UserPassesTestMixin, View):

    # Só atendentes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Ação de chamar é um POST, pois modifica o estado do recurso.
    def post(self, request, *args, **kwargs):
        pk_fila = self.kwargs.get('pk') # Pk da FilaAtendimento.
        item_fila = get_object_or_404(FilaAtendimento, pk=pk_fila)

        if item_fila.status == 'AGUARDANDO':
            item_fila.status = 'EM_ATENDIMENTO'
            item_fila.data_hora_chamada = timezone.now() # Registra a hora da chamada.
            item_fila.save()
            messages.success(request, f"Paciente {item_fila.paciente.nome_completo} chamado com sucesso!")
        else:
            messages.warning(request, f"O paciente {item_fila.paciente.nome_completo} não estava aguardando.")

        return redirect('painel_atendente') # Volta para o painel.

# View de detalhes do atendimento, usada pelo MÉDICO.
# É aqui que o médico vê os dados do paciente, a fila dele, e registra informações do atendimento.
class AtendimentoDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = FilaAtendimento # O objeto principal desta view é um item da FilaAtendimento.
    template_name = 'medico_painel.html' # O "painel do médico" é, na verdade, o detalhe de um atendimento.
    context_object_name = 'atendimento' # Nome do objeto no template.

    # Só médicos.
    def test_func(self):
        return self.request.user.groups.filter(name='Médicos').exists()

    # Adiciono muitas informações ao contexto para o template do médico.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        atendimento_atual = self.object # O item da FilaAtendimento sendo visualizado.

        context['paciente'] = atendimento_atual.paciente # Objeto Paciente para fácil acesso.

        try:
            # Pego a fila específica do médico deste atendimento, excluindo o atendimento atual.
            medico_para_fila = atendimento_atual.medico_destino
            if medico_para_fila:
                fila_do_medico = FilaAtendimento.objects.filter(
                    medico_destino=medico_para_fila,
                    status__in=['AGUARDANDO', 'EM_ATENDIMENTO'] # Apenas os que estão na fila ou sendo atendidos.
                ).exclude(pk=atendimento_atual.pk).order_by('-status', 'data_hora_chegada') # EM_ATENDIMENTO primeiro, depois por chegada.
                context['fila_do_medico'] = fila_do_medico
            else:
                context['fila_do_medico'] = FilaAtendimento.objects.none() # Fila vazia se não tiver médico.
        except Medico.DoesNotExist: # Se, por algum motivo, o médico não existir.
            context['fila_do_medico'] = FilaAtendimento.objects.none()

        # Lista de exames pré-definidos para o médico selecionar.
        # Poderia vir de um modelo no futuro, mas por enquanto está hardcoded.
        lista_de_exames_disponiveis = [
            "Hemograma Completo", "Glicose em Jejum", "TTOG", "HbA1C", "Frutosamina",
            "Insulina", "Ureia", "Creatinina", "Ácido Úrico", "Triglicerídeos",
            "HDL-C", "Colesterol Total", "Colesterol Não HDL-C", "TGO/AST", "Cálcio",
            "Bilirrubina Total e Frações", "Fosfatase Alcalina", "GGT", "Transferrina",
            "Ferro", "Ferritina", "Vitamina B12", "Homocisteína", "Vitamina D",
            "Magnésio", "Potássio", "Fósforo", "TSH", "T3 e T4 Livre", "Sódio"
        ]
        context['exames_disponiveis'] = lista_de_exames_disponiveis

        # Para carregar os exames e notas já salvos anteriormente neste atendimento.
        context['selecionados_checkbox_salvos'] = atendimento_atual.exames_checkbox_selecionados or []
        context['outro_digitado_salvo'] = atendimento_atual.exame_outro_digitado or ""
        context['evolucao_consulta_salva'] = atendimento_atual.evolucao_consulta or ""
        context['conduta_adotada_salva'] = atendimento_atual.conduta_adotada or ""

        return context

    # Método POST para salvar os dados que o médico inseriu (exames, evolução, conduta).
    def post(self, request, *args, **kwargs):
        atendimento = self.get_object() # Pego o objeto FilaAtendimento atual.

        # Pego os dados do formulário.
        exames_selecionados_checkbox = request.POST.getlist('exames_selecionados') # Lista de checkboxes.
        outro_exame_texto = request.POST.get('exame_outro_texto', '').strip() # Campo de texto "outro exame".

        atendimento.exames_checkbox_selecionados = exames_selecionados_checkbox
        if outro_exame_texto:
            atendimento.exame_outro_digitado = outro_exame_texto
        else:
            atendimento.exame_outro_digitado = None # Garanto que fique nulo se vazio.

        atendimento.evolucao_consulta = request.POST.get('evolucao_consulta', '').strip()
        atendimento.conduta_adotada = request.POST.get('conduta_adotada', '').strip()

        atendimento.save() # Salvo as alterações no objeto FilaAtendimento.
        messages.success(request, "Dados do atendimento (exames e notas) foram salvos com sucesso!")

        # Redireciono para a mesma página (detalhe do atendimento) para mostrar os dados salvos.
        return redirect('atendimento_detalhe', pk=atendimento.pk)

# View para o Médico "finalizar" um atendimento.
# Muda o status para 'ATENDIDO'.
class FinalizarAtendimentoView(LoginRequiredMixin, UserPassesTestMixin, View):

    # Só médicos.
    def test_func(self):
        return self.request.user.groups.filter(name='Médicos').exists()

    # Ação de finalizar é um POST.
    def post(self, request, *args, **kwargs):
        pk_atendimento = self.kwargs.get('pk') # Pk do FilaAtendimento.
        atendimento = get_object_or_404(FilaAtendimento, pk=pk_atendimento)

        paciente_nome = atendimento.paciente.nome_completo # Para as mensagens.

        # Lógica para finalizar dependendo do status atual.
        if atendimento.status == 'AGUARDANDO':
            # Se estava aguardando e o médico finalizou direto (ex: paciente não veio, mas quer registrar).
            atendimento.status = 'ATENDIDO'
            if not atendimento.data_hora_chamada: # Se não foi chamado formalmente antes.
                atendimento.data_hora_chamada = timezone.now()
            atendimento.data_hora_fim = timezone.now() # Registra hora do fim.
            atendimento.save()
            messages.success(request, f"Atendimento (que estava aguardando) do paciente {paciente_nome} finalizado com sucesso.")

        elif atendimento.status == 'EM_ATENDIMENTO':
            # Fluxo normal: estava em atendimento e foi finalizado.
            atendimento.status = 'ATENDIDO'
            atendimento.data_hora_fim = timezone.now()
            atendimento.save()
            messages.success(request, f"Atendimento do paciente {paciente_nome} finalizado com sucesso.")

        elif atendimento.status == 'ATENDIDO':
            messages.info(request, f"Este atendimento para {paciente_nome} já foi finalizado anteriormente.")

        elif atendimento.status == 'CANCELADO':
            messages.warning(request, f"Este atendimento para {paciente_nome} está cancelado e não pode ser finalizado desta forma.")

        else:
            # Caso haja algum status inesperado.
            messages.error(request, f"Status desconhecido para o atendimento de {paciente_nome}. Nenhuma ação realizada.")

        return redirect('home') # Após finalizar, volta para a home do médico.

# View para listar os Pacientes cadastrados, com funcionalidade de busca.
# Usada pelos Atendentes.
class PacienteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Paciente
    template_name = 'paciente_list.html'
    context_object_name = 'pacientes_list'
    paginate_by = 10 # Paginação.

    # Só atendentes.
    def test_func(self):
        return self.request.user.groups.filter(name='Atendentes').exists()

    # Define o queryset, aplicando filtro de busca se houver.
    def get_queryset(self):
        queryset = Paciente.objects.all().order_by('nome_completo') # Todos os pacientes, ordenados por nome.

        query = self.request.GET.get('q') # Pego o parâmetro de busca 'q' da URL.
        if query:
            # Se tem query, filtro por nome completo OU carteira do SUS.
            # Uso Q objects para o OR. `icontains` é case-insensitive.
            queryset = queryset.filter(
                Q(nome_completo__icontains=query) |
                Q(carteira_sus__icontains=query)
            )
            # Debug para ver o que está acontecendo.
            print(f"DEBUG PacienteListView: Buscando por '{query}', encontrados: {queryset.count()}")
        else:
            print("DEBUG PacienteListView: Listando todos os pacientes (sem filtro de busca).")

        return queryset

    # Adiciono o termo de busca ao contexto para poder exibi-lo no campo de busca novamente.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '') # Se não houver 'q', usa string vazia.
        return context

