# Gestor de Filas para Consultórios Médicos

## Descrição

O "Gestor de Filas" é um sistema web desenvolvido com o framework Django para facilitar o gerenciamento de filas de atendimento em consultórios médicos. Ele permite o cadastro e organização de pacientes, a atribuição a médicos específicos, o acompanhamento do status de cada atendimento, e possui interfaces distintas para os papéis de Atendente e Médico, garantindo um fluxo de trabalho eficiente.

## Tecnologias Utilizadas

* **Backend:**
    * Python 3.13
    * Django 5.2.1
    * SQLite
* **Frontend:**
    * HTML5
    * CSS3
    * Bootstrap 5 (via CDN, para estilização e responsividade)
    * JavaScript 
* **Bibliotecas Python Adicionais:**
    * `django-widget-tweaks`
* **Outros:**
    * Font Awesome
    * Ambiente Virtual Python
    * Git & GitHub para versionamento

## Funcionalidades Implementadas (Até o Momento)

* **Autenticação e Autorização:**
    * Sistema de Login e Logout para usuários.
    * Controle de acesso baseado em grupos ('Atendentes', 'Médicos') utilizando `UserPassesTestMixin`.
    * Páginas iniciais (`home`) personalizadas de acordo com o grupo do usuário logado.

* **Módulo da Atendente:**
    * **Gerenciamento de Pacientes:**
        * Cadastro de novos pacientes.
        * Listagem e busca de pacientes existentes (por nome ou Nº SUS).
        * Edição dos dados cadastrais de pacientes.
    * **Gerenciamento de Fila:**
        * Visualização do painel de atendimento com a lista de pacientes aguardando.
        * Filtro da fila por médico específico.
        * Adicionar um paciente (buscado na lista) à fila de um médico específico, com opção de adicionar observações.
        * Funcionalidade "Chamar Paciente" (altera o status do atendimento para 'Em Atendimento' e registra a hora da chamada).

* **Módulo do Médico:**
    * Visualização detalhada de um atendimento específico (focado no objeto `FilaAtendimento`), mostrando:
        * Dados completos do paciente associado.
        * Status atual do atendimento.
    * Barra lateral ("Fila a Seguir") mostrando outros pacientes atribuídos ao médico logado (status 'Aguardando' ou 'Em Atendimento').
    * **Solicitação de Exames:**
        * Formulário com checkboxes para exames pré-definidos.
        * Campo "Outro Exame" para exames não listados.
        * Salvamento dos exames solicitados (checkboxes e texto do campo "Outro") associados ao atendimento.
    * Funcionalidade **"Finalizar Atendimento"** (altera o status para 'Atendido' e registra a hora de finalização).

## Configuração e Instalação do Ambiente Local

Siga os passos abaixo para configurar e rodar o projeto em sua máquina local:

1.  **Clonar o Repositório:**
    ```bash
    git clone (https://github.com/usuario/repositorio.git)
    cd repositorio
    ```
    *(Substitua `usuario/repositorio` pelo URL real do seu projeto)*

2.  **Criar e Ativar o Ambiente Virtual:**
    ```bash
    python -m venv venv
    ```
    * No Windows:
        ```bash
        venv\Scripts\activate
        ```
    * No Linux ou macOS:
        ```bash
        source venv/bin/activate
        ```

3.  **Instalar as Dependências:**
    (Certifique-se de que o arquivo `requirements.txt` está atualizado no seu projeto)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Aplicar as Migrações do Banco de Dados:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Criar um Superusuário (Administrador):**
    ```bash
    python manage.py createsuperuser
    ```
    Siga as instruções para definir nome de usuário, email e senha.

6.  **Configurar Grupos e Usuários de Teste (Via Admin):**
    * Acesse o painel de administração: `http://127.0.0.1:8000/admin/`
    * Faça login com o superusuário criado.
    * Crie os grupos: "Atendentes" e "Médicos".
    * Crie usuários de teste e associe-os a esses grupos para testar as diferentes funcionalidades e permissões. Lembre-se de criar também os perfis `Medico` para os usuários do grupo "Médicos".

7.  **Rodar o Servidor de Desenvolvimento:**
    ```bash
    python manage.py runserver
    ```
    O sistema estará acessível em `http://127.0.0.1:8000/`.

## Como Usar (Visão Geral)

* **Atendente:** Após o login, será direcionado(a) para uma página inicial com opções para "Gerenciar Pacientes" (listar/buscar/cadastrar/editar) e "Ver Fila Atual" (painel de atendimento). No painel, pode filtrar por médico, chamar pacientes e adicionar pacientes existentes à fila.
* **Médico:** Após o login, será direcionado(a) para uma página inicial. A principal interação ocorre ao acessar a tela de um atendimento específico (ex: `/atendimento/ID_DO_ATENDIMENTO/`), onde pode ver detalhes do paciente, sua fila, solicitar exames e finalizar o atendimento.

## Próximos Passos / Funcionalidades Futuras (Sugestões)

* **[ ]** Implementar a funcionalidade "Deletar Paciente" (com as devidas confirmações).
* **[ ]** Refinar o fluxo de adição de paciente pela atendente para que, após o cadastro de um *novo* paciente, ela seja direcionada para a tela de "Adicionar à Fila" para aquele paciente.
* **[ ]** Permitir que o médico edite/adicione observações e outras informações da consulta diretamente na tela de atendimento (além dos exames).
* **[ ]** Melhorar a navegação para o médico (ex: um link "Próximo Paciente" na tela de atendimento).
* **[ ]** Implementar o "envio" do paciente para o médico em tempo real usando Django Channels (WebSockets).
* **[ ]** Aplicar CSS personalizado para alinhar o visual com os designs do Figma.
* **[ ]** **Multi-Tenancy:** Adaptar o sistema para que possa ser usado por múltiplos consultórios independentes (funcionalidade planejada para o futuro).
* **[ ]** Testes automatizados.
* **[ ]** Documentação mais detalhada do código.
