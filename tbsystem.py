import customtkinter as ctk
import threading
import time
import imaplib
import email
import os
import re
import json
import webbrowser
from email.header import decode_header
from cryptography.fernet import Fernet
from datetime import datetime
from tkinter import messagebox
import queue
from PIL import Image
import io

# --- PALETA DE CORES ATUALIZADA (Design Moderno) ---
CORES = {
    "fundo_escuro": "#0A0F1F",      # Azul escuro profundo
    "sidebar": "#1A1F33",           # Azul marinho com mais profundidade
    "card": "#232842",              # Cor para cards
    "primaria": "#3F51B5",          # Roxo/azul primário vibrante
    "primaria_hover": "#5C6BC0",    # Versão mais clara do primário
    "secundaria": "#7C4DFF",        # Roxo vibrante para destaques
    "sucesso": "#00BFA6",           # Verde azulado suave
    "sucesso_hover": "#1DE9B6",     # Versão mais clara do sucesso
    "perigo": "#FF5252",            # Vermelho suave
    "perigo_hover": "#FF8A80",      # Versão mais clara do perigo
    "aviso": "#FFB74D",             # Laranja suave
    "texto_primario": "#FFFFFF",    # Branco
    "texto_secundario": "#B0B8D9",  # Cinza azulado claro
    "borda": "#2E3550"              # Cor para bordas
}

# --- CONFIGURAÇÕES GLOBAIS ---
PADRAO_REGEX = r"^\d{2}\.\d{2}\s[A-Z\s]+\sNF\s\d+"
ARQUIVO_DADOS = "vault.json"
CHAVE_FILE = "secret.key"
RAIZ_TRIAGEM = r"C:\Teste\04_2026\TRIAGEM_2026\100-3JM"

class SecurityManager:
    @staticmethod
    def get_key():
        if not os.path.exists(CHAVE_FILE):
            key = Fernet.generate_key()
            with open(CHAVE_FILE, "wb") as f: 
                f.write(key)
        return open(CHAVE_FILE, "rb").read()

    @classmethod
    def encrypt(cls, texto):
        if not texto: return ""
        f = Fernet(cls.get_key())
        return f.encrypt(texto.encode()).decode()

    @classmethod
    def decrypt(cls, texto_cifrado):
        if not texto_cifrado: return ""
        f = Fernet(cls.get_key())
        try: 
            return f.decrypt(texto_cifrado.encode()).decode()
        except: 
            return ""

class CardConta(ctk.CTkFrame):
    """Card estilizado para exibir contas"""
    def __init__(self, master, conta, on_delete, **kwargs):
        super().__init__(master, fg_color=CORES["card"], corner_radius=12, border_width=1, border_color=CORES["borda"], **kwargs)
        
        self.conta = conta
        self.on_delete = on_delete
        
        # Layout do card
        self.grid_columnconfigure(1, weight=1)
        
        # Ícone (simulado com texto)
        self.icon_label = ctk.CTkLabel(self, text="📧", font=("Segoe UI", 20), width=40)
        self.icon_label.grid(row=0, column=0, padx=(15, 5), pady=15)
        
        # Informações da conta
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="w", padx=5, pady=15)
        
        self.email_label = ctk.CTkLabel(self.info_frame, text=conta['user'], 
                                        font=("Segoe UI", 14, "bold"), 
                                        text_color=CORES["texto_primario"])
        self.email_label.pack(anchor="w")
        
        self.status_label = ctk.CTkLabel(self.info_frame, text="● Ativa", 
                                         font=("Segoe UI", 11), 
                                         text_color=CORES["sucesso"])
        self.status_label.pack(anchor="w")
        
        # Botão deletar estilizado
        self.btn_delete = ctk.CTkButton(self, text="✕", width=32, height=32,
                                        fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"],
                                        font=("Segoe UI", 16, "bold"), corner_radius=8,
                                        command=self.confirmar_delete)
        self.btn_delete.grid(row=0, column=2, padx=(5, 15), pady=15)
        
        # Hover effect
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        self.configure(border_color=CORES["primaria"])
    
    def on_leave(self, e):
        self.configure(border_color=CORES["borda"])
    
    def confirmar_delete(self):
        if messagebox.askyesno("Confirmar", f"Remover conta {self.conta['user']}?"):
            self.on_delete()

class CardFornecedor(ctk.CTkFrame):
    """Card estilizado para exibir fornecedores"""
    def __init__(self, master, fornecedor, on_delete, **kwargs):
        super().__init__(master, fg_color=CORES["card"], corner_radius=12, border_width=1, border_color=CORES["borda"], **kwargs)
        
        self.fornecedor = fornecedor
        self.on_delete = on_delete
        
        # Layout
        self.grid_columnconfigure(1, weight=1)
        
        # Ícone
        self.icon_label = ctk.CTkLabel(self, text="🏢", font=("Segoe UI", 20), width=40)
        self.icon_label.grid(row=0, column=0, padx=(15, 5), pady=15)
        
        # Nome do fornecedor
        self.nome_label = ctk.CTkLabel(self, text=fornecedor, font=("Segoe UI", 14), text_color=CORES["texto_primario"], wraplength=300)
        self.nome_label.grid(row=0, column=1, sticky="w", padx=5, pady=15)
        
        # Botão deletar
        self.btn_delete = ctk.CTkButton(self, text="✕", width=32, height=32, fg_color=CORES["perigo"], hover_color=CORES["perigo_hover"], font=("Segoe UI", 16, "bold"), corner_radius=8, command=self.confirmar_delete)
        self.btn_delete.grid(row=0, column=2, padx=(5, 15), pady=15)
        
        # Hover effect
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        self.configure(border_color=CORES["primaria"])
    
    def on_leave(self, e):
        self.configure(border_color=CORES["borda"])
    
    def confirmar_delete(self):
        if messagebox.askyesno("Confirmar", f"Remover fornecedor {self.fornecedor}?"):
            self.on_delete()

class DashboardCard(ctk.CTkFrame):
    """Card para métricas no dashboard"""
    def __init__(self, master, titulo, valor, icone="📊", **kwargs):
        super().__init__(master, fg_color=CORES["card"], corner_radius=15, border_width=1, border_color=CORES["borda"], **kwargs)
        
        # Ícone
        self.icon_label = ctk.CTkLabel(self, text=icone, font=("Segoe UI", 28), text_color=CORES["secundaria"])
        self.icon_label.pack(pady=(20, 10))
        
        # Valor
        self.valor_label = ctk.CTkLabel(self, text=str(valor), 
                                        font=("Segoe UI", 32, "bold"), 
                                        text_color=CORES["texto_primario"])
        self.valor_label.pack()
        
        # Título
        self.titulo_label = ctk.CTkLabel(self, text=titulo, 
                                         font=("Segoe UI", 13), 
                                         text_color=CORES["texto_secundario"])
        self.titulo_label.pack(pady=(5, 20))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TB System | Versão 2026")
        self.geometry("1300x850")
        self.minsize(1100, 700)
        
        # Configurações de aparência
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=CORES["fundo_escuro"])
        
        self.contas = self.carregar_dados()
        self.monitorando = False
        self.log_queue = queue.Queue()
        self.estatisticas = {"total_nfs": 0, "erros": 0, "ativos": 0}
        
        self.setup_ui()
        self.atualizar_estatisticas()
        self.after(100, self.processar_log_queue)
        self.log("🚀 TB System iniciado com sucesso")

    def setup_ui(self):
        # Configuração do grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar com design moderno ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=CORES["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo e título
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        self.logo_frame.pack(fill="x", pady=(30, 20))
        
        ctk.CTkLabel(self.logo_frame, text="⚡", font=("Segoe UI", 48), text_color=CORES["secundaria"]).pack()
        ctk.CTkLabel(self.logo_frame, text="TB SYSTEM", 
                     font=("Segoe UI", 22, "bold"), 
                     text_color=CORES["texto_primario"]).pack()
        ctk.CTkLabel(self.logo_frame, text="Triagem Automática", 
                     font=("Segoe UI", 11), 
                     text_color=CORES["texto_secundario"]).pack()

        # Separador
        self.separador = ctk.CTkFrame(self.sidebar, height=2, fg_color=CORES["borda"])
        self.separador.pack(fill="x", padx=20, pady=20)

        # Botões principais
        self.btn_toggle = ctk.CTkButton(self.sidebar, 
                                        text="▶ INICIAR TRIAGEM", 
                                        height=50,
                                        fg_color=CORES["sucesso"], 
                                        hover_color=CORES["sucesso_hover"],
                                        font=("Segoe UI", 14, "bold"),
                                        corner_radius=12,
                                        command=self.toggle_engine)
        self.btn_toggle.pack(pady=10, padx=20, fill="x")

        self.btn_folder = ctk.CTkButton(self.sidebar, 
                                        text="📁 ABRIR PASTA RAIZ", 
                                        height=45,
                                        fg_color="transparent",
                                        border_width=2,
                                        border_color=CORES["primaria"],
                                        text_color=CORES["texto_primario"],
                                        hover_color=CORES["primaria"],
                                        font=("Segoe UI", 12, "bold"),
                                        corner_radius=12,
                                        command=self.abrir_pasta)
        self.btn_folder.pack(pady=10, padx=20, fill="x")

        # Indicador de status
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.pack(pady=20, fill="x")
        
        self.status_indicator = ctk.CTkLabel(self.status_frame, 
                                            text="● Sistema em Espera", 
                                            text_color=CORES["perigo"],
                                            font=("Segoe UI", 12, "bold"))
        self.status_indicator.pack()
        
        self.stats_frame = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        self.stats_frame.pack(pady=10)
        
        self.stats_nfs = ctk.CTkLabel(self.stats_frame, 
                                      text="NFS: 0", 
                                      text_color=CORES["texto_secundario"])
        self.stats_nfs.pack()

        # --- Abas customizadas com design moderno ---
        self.tabview = ctk.CTkTabview(self, 
                                      fg_color="transparent",
                                      segmented_button_fg_color=CORES["sidebar"],
                                      segmented_button_selected_color=CORES["primaria"],
                                      segmented_button_unselected_color=CORES["card"],
                                      segmented_button_unselected_hover_color=CORES["primaria_hover"],
                                      segmented_button_selected_hover_color=CORES["primaria_hover"],
                                      corner_radius=12)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Configurar cores das abas
        self.tabview._segmented_button.configure(font=("Segoe UI", 12, "bold"))
        
        self.tab_dash = self.tabview.add("📊 Dashboard")
        self.tab_config = self.tabview.add("📧 Contas de Email")
        self.tab_filtros = self.tabview.add("🏢 Fornecedores")

        self.setup_tab_dash()
        self.setup_tab_config()
        self.setup_tab_filtros()

    def setup_tab_dash(self):
        """Dashboard com métricas e logs"""
        # Frame para métricas
        self.metricas_frame = ctk.CTkFrame(self.tab_dash, fg_color="transparent")
        self.metricas_frame.pack(fill="x", padx=20, pady=20)
        
        self.metricas_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        # Cards de métricas
        self.card_nfs = DashboardCard(self.metricas_frame, "NFS Processadas", "0", "📄")
        self.card_nfs.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.card_erros = DashboardCard(self.metricas_frame, "Erros", "0", "⚠️")
        self.card_erros.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.card_contas = DashboardCard(self.metricas_frame, "Contas Ativas", str(len(self.contas["minhas_contas"])), "📧")
        self.card_contas.grid(row=0, column=2, padx=5, sticky="ew")
        
        self.card_forn = DashboardCard(self.metricas_frame, "Fornecedores", str(len(self.contas["fornecedores"])), "🏢")
        self.card_forn.grid(row=0, column=3, padx=5, sticky="ew")

        # Área de logs
        self.log_frame = ctk.CTkFrame(self.tab_dash, fg_color=CORES["card"], corner_radius=15)
        self.log_frame.pack(expand=True, fill="both", padx=20, pady=(0,20))
        
        # Título da seção de logs
        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent", height=40)
        log_header.pack(fill="x", padx=15, pady=(15,5))
        
        ctk.CTkLabel(log_header, text="📋 LOG DO SISTEMA", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color=CORES["texto_primario"]).pack(side="left")
        
        # Botão limpar logs
        ctk.CTkButton(log_header, text="Limpar", width=70, height=28,
                     fg_color="transparent", border_width=1, border_color=CORES["borda"],
                     text_color=CORES["texto_secundario"], hover_color=CORES["primaria"],
                     command=self.limpar_logs).pack(side="right")
        
        # Textbox de logs com design melhorado
        self.log_view = ctk.CTkTextbox(self.log_frame, 
                                       font=("Consolas", 12), 
                                       state="disabled", 
                                       fg_color=CORES["fundo_escuro"],
                                       border_color=CORES["borda"],
                                       border_width=1,
                                       corner_radius=10,
                                       text_color=CORES["texto_secundario"])
        self.log_view.pack(expand=True, fill="both", padx=15, pady=15)

    def setup_tab_config(self):
        """Configuração de contas de email"""
        # Frame de adição com design moderno
        f_add = ctk.CTkFrame(self.tab_config, fg_color=CORES["card"], corner_radius=15)
        f_add.pack(fill="x", padx=20, pady=20)
        
        # Título da seção
        ctk.CTkLabel(f_add, text="➕ ADICIONAR NOVA CONTA", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color=CORES["texto_primario"]).pack(anchor="w", padx=20, pady=(20,15))
        
        # Grid para os campos
        campos_frame = ctk.CTkFrame(f_add, fg_color="transparent")
        campos_frame.pack(fill="x", padx=20, pady=(0,20))
        campos_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.ent_email = ctk.CTkEntry(campos_frame, 
                                      placeholder_text="📧 E-mail", 
                                      height=40,
                                      fg_color=CORES["fundo_escuro"],
                                      border_color=CORES["borda"],
                                      corner_radius=10,
                                      font=("Segoe UI", 12))
        self.ent_email.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.ent_pass = ctk.CTkEntry(campos_frame, 
                                     placeholder_text="🔑 Senha de App", 
                                     show="*", 
                                     height=40,
                                     fg_color=CORES["fundo_escuro"],
                                     border_color=CORES["borda"],
                                     corner_radius=10,
                                     font=("Segoe UI", 12))
        self.ent_pass.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.btn_add_conta = ctk.CTkButton(campos_frame, 
                                          text="Conectar Conta", 
                                          height=40,
                                          fg_color=CORES["primaria"], 
                                          hover_color=CORES["primaria_hover"],
                                          corner_radius=10,
                                          font=("Segoe UI", 12, "bold"),
                                          command=self.add_conta)
        self.btn_add_conta.grid(row=0, column=2, padx=5, sticky="ew")

        # Área de contas cadastradas
        contas_header = ctk.CTkFrame(self.tab_config, fg_color="transparent", height=30)
        contas_header.pack(fill="x", padx=20, pady=(20,10))
        
        ctk.CTkLabel(contas_header, text="📋 CONTAS CADASTRADAS", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color=CORES["texto_primario"]).pack(side="left")

        self.scroll_contas = ctk.CTkScrollableFrame(self.tab_config, 
                                                    fg_color="transparent",
                                                    corner_radius=10)
        self.scroll_contas.pack(fill="both", expand=True, padx=20, pady=(0,20))
        self.renderizar_contas()

    def setup_tab_filtros(self):
        """Configuração de fornecedores"""
        # Frame de adição com design moderno
        f_add = ctk.CTkFrame(self.tab_filtros, fg_color=CORES["card"], corner_radius=15)
        f_add.pack(fill="x", padx=20, pady=20)
        
        # Título da seção
        ctk.CTkLabel(f_add, text="➕ ADICIONAR FORNECEDOR", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color=CORES["texto_primario"]).pack(anchor="w", padx=20, pady=(20,15))
        
        # Campos
        campos_frame = ctk.CTkFrame(f_add, fg_color="transparent")
        campos_frame.pack(fill="x", padx=20, pady=(0,20))
        campos_frame.grid_columnconfigure((0,1), weight=1)
        
        self.ent_forn = ctk.CTkEntry(campos_frame, 
                                     placeholder_text="exemplo@fornecedor.com.br", 
                                     height=40,
                                     fg_color=CORES["fundo_escuro"],
                                     border_color=CORES["borda"],
                                     corner_radius=10,
                                     font=("Segoe UI", 12))
        self.ent_forn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.btn_add_forn = ctk.CTkButton(campos_frame, 
                                         text="Cadastrar Fornecedor", 
                                         height=40,
                                         fg_color=CORES["primaria"], 
                                         hover_color=CORES["primaria_hover"],
                                         corner_radius=10,
                                         font=("Segoe UI", 12, "bold"),
                                         command=self.add_filtro)
        self.btn_add_forn.grid(row=0, column=1, padx=5, sticky="ew")

        # Área de fornecedores cadastrados
        forn_header = ctk.CTkFrame(self.tab_filtros, fg_color="transparent", height=30)
        forn_header.pack(fill="x", padx=20, pady=(20,10))
        
        ctk.CTkLabel(forn_header, text="📋 FORNECEDORES CADASTRADOS", 
                    font=("Segoe UI", 14, "bold"), 
                    text_color=CORES["texto_primario"]).pack(side="left")

        self.scroll_forn = ctk.CTkScrollableFrame(self.tab_filtros, 
                                                  fg_color="transparent",
                                                  corner_radius=10)
        self.scroll_forn.pack(fill="both", expand=True, padx=20, pady=(0,20))
        self.renderizar_fornecedores()

    def renderizar_contas(self):
        """Renderiza cards de contas"""
        for widget in self.scroll_contas.winfo_children():
            widget.destroy()
            
        if not self.contas["minhas_contas"]:
            frame_vazio = ctk.CTkFrame(self.scroll_contas, fg_color="transparent")
            frame_vazio.pack(fill="both", expand=True, pady=50)
            ctk.CTkLabel(frame_vazio, 
                        text="✨ Nenhuma conta cadastrada", 
                        font=("Segoe UI", 14), 
                        text_color=CORES["texto_secundario"]).pack()
            return
            
        for i, conta in enumerate(self.contas["minhas_contas"]):
            card = CardConta(self.scroll_contas, conta, lambda idx=i: self.remover_conta(idx))
            card.pack(fill="x", pady=5)

    def renderizar_fornecedores(self):
        """Renderiza cards de fornecedores"""
        for widget in self.scroll_forn.winfo_children():
            widget.destroy()
            
        if not self.contas["fornecedores"]:
            frame_vazio = ctk.CTkFrame(self.scroll_forn, fg_color="transparent")
            frame_vazio.pack(fill="both", expand=True, pady=50)
            ctk.CTkLabel(frame_vazio, 
                        text="✨ Nenhum fornecedor cadastrado", 
                        font=("Segoe UI", 14), 
                        text_color=CORES["texto_secundario"]).pack()
            return
            
        for i, forn in enumerate(self.contas["fornecedores"]):
            card = CardFornecedor(self.scroll_forn, forn, lambda idx=i: self.remover_filtro(idx))
            card.pack(fill="x", pady=5)

    def atualizar_estatisticas(self):
        """Atualiza os cards de estatísticas"""
        self.card_nfs.valor_label.configure(text=str(self.estatisticas["total_nfs"]))
        self.card_erros.valor_label.configure(text=str(self.estatisticas["erros"]))
        self.card_contas.valor_label.configure(text=str(len(self.contas["minhas_contas"])))
        self.card_forn.valor_label.configure(text=str(len(self.contas["fornecedores"])))
        
        self.stats_nfs.configure(text=f"NFS: {self.estatisticas['total_nfs']}")

    def limpar_logs(self):
        """Limpa a área de logs"""
        self.log_view.configure(state="normal")
        self.log_view.delete("1.0", "end")
        self.log_view.configure(state="disabled")

    def log(self, msg):
        """Adiciona mensagem ao log com timestamp"""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {msg}")

    def processar_log_queue(self):
        """Processa fila de logs na thread principal"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_view.configure(state="normal")
                self.log_view.insert("end", msg + "\n")
                self.log_view.see("end")
                self.log_view.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.processar_log_queue)

    def add_conta(self):
        """Adiciona nova conta"""
        e = self.ent_email.get().strip()
        p = self.ent_pass.get().strip()
        
        if not e or not p:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return
            
        if not self.validar_email(e):
            messagebox.showwarning("Aviso", "Formato de e-mail inválido!")
            return
            
        self.contas["minhas_contas"].append({
            "user": e, 
            "pass": SecurityManager.encrypt(p)
        })
        self.salvar_dados()
        self.renderizar_contas()
        
        self.ent_email.delete(0, 'end')
        self.ent_pass.delete(0, 'end')
        self.atualizar_estatisticas()
        
        self.log(f"✅ Conta {e} adicionada com sucesso")

    def remover_conta(self, index):
        """Remove conta"""
        conta = self.contas["minhas_contas"].pop(index)
        self.salvar_dados()
        self.renderizar_contas()
        self.atualizar_estatisticas()
        self.log(f"🗑️ Conta {conta['user']} removida")

    def add_filtro(self):
        """Adiciona novo fornecedor"""
        f = self.ent_forn.get().strip().lower()
        
        if not f:
            messagebox.showwarning("Aviso", "Digite um e-mail de fornecedor!")
            return
            
        if not self.validar_email(f):
            messagebox.showwarning("Aviso", "Formato de e-mail inválido!")
            return
            
        if f in self.contas["fornecedores"]:
            messagebox.showwarning("Aviso", "Fornecedor já cadastrado!")
            return
            
        self.contas["fornecedores"].append(f)
        self.salvar_dados()
        self.renderizar_fornecedores()
        self.ent_forn.delete(0, 'end')
        self.atualizar_estatisticas()
        self.log(f"🎯 Fornecedor {f} cadastrado")

    def remover_filtro(self, index):
        """Remove fornecedor"""
        forn = self.contas["fornecedores"].pop(index)
        self.salvar_dados()
        self.renderizar_fornecedores()
        self.atualizar_estatisticas()
        self.log(f"🗑️ Fornecedor {forn} removido")

    def validar_email(self, email):
        """Valida formato de email"""
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(padrao, email) is not None

    def abrir_pasta(self):
        """Abre a pasta raiz"""
        try:
            os.makedirs(RAIZ_TRIAGEM, exist_ok=True)
            webbrowser.open(os.path.realpath(RAIZ_TRIAGEM))
            self.log("📂 Pasta raiz aberta")
        except Exception as e:
            self.log(f"❌ Erro ao abrir pasta: {str(e)}")

    def carregar_dados(self):
        """Carrega dados salvos"""
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"minhas_contas": [], "fornecedores": []}

    def salvar_dados(self):
        """Salva dados"""
        with open(ARQUIVO_DADOS, "w") as f:
            json.dump(self.contas, f, indent=2)

    def toggle_engine(self):
        """Liga/desliga o monitoramento"""
        if not self.contas["minhas_contas"]:
            messagebox.showwarning("Aviso", "Cadastre pelo menos uma conta primeiro!")
            return
            
        if not self.contas["fornecedores"]:
            messagebox.showwarning("Aviso", "Cadastre pelo menos um fornecedor primeiro!")
            return
            
        self.monitorando = not self.monitorando
        
        if self.monitorando:
            self.btn_toggle.configure(
                text="⏸ PARAR TRIAGEM", 
                fg_color=CORES["perigo"],
                hover_color=CORES["perigo_hover"]
            )
            self.status_indicator.configure(
                text="● Sistema Ativo", 
                text_color=CORES["sucesso"]
            )
            self.log("🚀 Iniciando monitoramento...")
            threading.Thread(target=self.main_loop, daemon=True).start()
        else:
            self.btn_toggle.configure(
                text="▶ INICIAR TRIAGEM", 
                fg_color=CORES["sucesso"],
                hover_color=CORES["sucesso_hover"]
            )
            self.status_indicator.configure(
                text="● Sistema Pausado", 
                text_color=CORES["perigo"]
            )
            self.log("⏸ Monitoramento pausado")

    def main_loop(self):
        """Loop principal de monitoramento"""
        while self.monitorando:
            for conta in self.contas["minhas_contas"]:
                if not self.monitorando:
                    break
                self.processar_caixa(conta)
            
            if self.monitorando:
                for i in range(60):
                    if not self.monitorando:
                        break
                    time.sleep(1)

    def processar_caixa(self, conta):
        """Processa caixa de email"""
        try:
            user = conta["user"]
            pw = SecurityManager.decrypt(conta["pass"])
            
            # Seleciona servidor
            if "@gmail" in user.lower():
                server = "imap.gmail.com"
            elif "@hotmail" in user.lower() or "@outlook" in user.lower():
                server = "outlook.office365.com"
            else:
                server = "imap.gmail.com"  # padrão
            
            # Conecta
            mail = imaplib.IMAP4_SSL(server)
            mail.login(user, pw)
            mail.select("inbox")
            
            # Busca não lidos
            _, data = mail.search(None, "UNSEEN")
            
            if data[0]:
                nfs_encontradas = 0
                for num in data[0].split():
                    _, msg_data = mail.fetch(num, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    from_header = msg.get("From")
                    nome_rem, email_rem = email.utils.parseaddr(from_header)
                    
                    if email_rem.lower() in self.contas["fornecedores"]:
                        self.triar_anexos(msg, nome_rem if nome_rem else email_rem)
                        nfs_encontradas += 1
                
                if nfs_encontradas > 0:
                    self.log(f"📬 {user}: {nfs_encontradas} NF(s) encontrada(s)")
            
            mail.logout()
            
        except Exception as e:
            self.log(f"❌ Erro em {conta['user']}: {str(e)[:50]}...")
            self.estatisticas["erros"] += 1

    def triar_anexos(self, msg, remetente):
        """Processa anexos dos emails"""
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            
            nome_arq = self.decodificar_nome(part.get_filename())
            if not nome_arq:
                continue
            
            if re.search(PADRAO_REGEX, nome_arq.upper()):
                nome_upper = nome_arq.upper()
                
                # Determina subpasta
                if "TOPOLÂNDIA" in nome_upper:
                    subpasta = "107 - TOPOLÂNDIA"
                elif "ADM" in nome_upper:
                    subpasta = "100 - 3JM"
                else:
                    subpasta = ""
                
                if not subpasta:
                    continue
                
                caminho_final = os.path.join(RAIZ_TRIAGEM, subpasta)
                
                try:
                    os.makedirs(caminho_final, exist_ok=True)
                    destino_arquivo = os.path.join(caminho_final, nome_arq)
                    
                    if os.path.exists(destino_arquivo):
                        self.log(f"⚠️ Arquivo duplicado: {nome_arq}")
                        continue
                    
                    # Salva arquivo
                    with open(destino_arquivo, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    
                    self.log(f"✅ NF salva: {nome_arq} -> {subpasta}")
                    self.estatisticas["total_nfs"] += 1
                    
                    # Atualiza estatísticas na thread principal
                    self.after(0, self.atualizar_estatisticas)
                    
                except Exception as e:
                    self.log(f"❌ Erro ao salvar {nome_arq}: {str(e)}")
                    self.estatisticas["erros"] += 1

    def decodificar_nome(self, nome):
        """Decodifica nome de arquivo"""
        if not nome:
            return None
        
        try:
            dec = decode_header(nome)[0]
            if isinstance(dec[0], bytes):
                return dec[0].decode(dec[1] or 'utf-8')
            return dec[0]
        except:
            return nome

if __name__ == "__main__":
    app = App()
    app.mainloop()a