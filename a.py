import customtkinter as ctk
import threading
import time
import imaplib
import email
import os
import re
import json
from email.header import decode_header
from cryptography.fernet import Fernet

PADRAO_REGEX = r"^\d{2}\.\d{2}\s[A-Z\s]+\sNF\s\d+"
ARQUIVO_DADOS = "vault.json"
CHAVE_FILE = "secret.key"

class SecurityManager:
    @staticmethod
    def get_key():
        if not os.path.exists(CHAVE_FILE):
            key = Fernet.generate_key()
            with open(CHAVE_FILE, "wb") as f: f.write(key)
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
        try: return f.decrypt(texto_cifrado.encode()).decode()
        except: return ""

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TriaBot NF | Sistema de Triagem Inteligente")
        self.geometry("1000x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.monitorando = False
        self.contas = self.carregar_dados()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🔍 TRIABOT NF", font=("Segoe UI", 22, "bold")).pack(pady=30)
        
        self.btn_toggle = ctk.CTkButton(self.sidebar, text="INICIAR TRIAGEM", height=45, 
                                         fg_color="#2ecc71", hover_color="#27ae60",
                                         font=("Segoe UI", 14, "bold"), command=self.toggle_engine)
        self.btn_toggle.pack(pady=10, padx=20, fill="x")

        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● Bot em Espera", text_color="#e74c3c", font=("Segoe UI", 12))
        self.status_indicator.pack(pady=5)

        ctk.CTkLabel(self.sidebar, text="TriaBot v2.0.1", font=("Segoe UI", 10), text_color="gray").pack(side="bottom", pady=20)

        self.tabview = ctk.CTkTabview(self, segmented_button_selected_color="#3b8ed0")
        self.tabview.grid(row=0, column=1, padx=20, pady=(10, 20), sticky="nsew")
        
        self.tab_dashboard = self.tabview.add("Painel de Triagem")
        self.tab_config = self.tabview.add("Contas & Conexão")
        self.tab_fornecedores = self.tabview.add("Filtros de Fornecedores")

        self.setup_dashboard()
        self.setup_config()
        self.setup_fornecedores()

    def setup_dashboard(self):
        ctk.CTkLabel(self.tab_dashboard, text="Logs de Processamento (Tempo Real)", font=("Segoe UI", 16, "bold")).pack(pady=(10,5), anchor="w", padx=20)
        self.log_view = ctk.CTkTextbox(self.tab_dashboard, font=("Consolas", 13), border_width=2, border_color="#333")
        self.log_view.pack(expand=True, fill="both", padx=20, pady=10)

    def setup_config(self):
        frame_conta = ctk.CTkFrame(self.tab_config)
        frame_conta.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(frame_conta, text="Vincular Conta para Monitoramento", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        self.ent_user = ctk.CTkEntry(frame_conta, placeholder_text="E-mail (Gmail/Outlook)", width=300)
        self.ent_user.grid(row=1, column=0, padx=10, pady=10)
        
        self.ent_pass = ctk.CTkEntry(frame_conta, placeholder_text="Senha de App", show="*", width=300)
        self.ent_pass.grid(row=1, column=1, padx=10, pady=10)
        
        ctk.CTkButton(frame_conta, text="+ Adicionar à Triagem", command=self.add_conta).grid(row=2, column=0, columnspan=2, pady=15)

        ctk.CTkLabel(self.tab_config, text="Contas Ativas", font=("Segoe UI", 14, "bold")).pack(pady=(10,0))
        self.contas_list = ctk.CTkTextbox(self.tab_config, height=150)
        self.contas_list.pack(fill="x", padx=20, pady=10)
        self.atualizar_contas_ui()

    def setup_fornecedores(self):
        ctk.CTkLabel(self.tab_fornecedores, text="Lista Branca de Remetentes", font=("Segoe UI", 14, "bold")).pack(pady=10)
        
        input_frame = ctk.CTkFrame(self.tab_fornecedores)
        input_frame.pack(fill="x", padx=20, pady=10)

        self.ent_remetente = ctk.CTkEntry(input_frame, placeholder_text="email@fornecedor.com", width=400)
        self.ent_remetente.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(input_frame, text="Autorizar", width=100, command=self.add_remetente).pack(side="left", padx=10)

        self.forn_list = ctk.CTkTextbox(self.tab_fornecedores, height=300)
        self.forn_list.pack(fill="both", expand=True, padx=20, pady=20)
        self.atualizar_fornecedores_ui()

    def carregar_dados(self):
        if os.path.exists(ARQUIVO_DADOS):
            with open(ARQUIVO_DADOS, "r") as f: return json.load(f)
        return {"minhas_contas": [], "fornecedores": []}

    def salvar_dados(self):
        with open(ARQUIVO_DADOS, "w") as f: json.dump(self.contas, f)

    def add_conta(self):
        user = self.ent_user.get().strip().lower()
        senha = self.ent_pass.get()
        if user and senha:
            self.contas["minhas_contas"].append({"user": user, "pass": SecurityManager.encrypt(senha)})
            self.salvar_dados()
            self.ent_user.delete(0, 'end'); self.ent_pass.delete(0, 'end')
            self.atualizar_contas_ui()
            self.log(f"Conta {user} vinculada ao bot.")

    def add_remetente(self):
        rem = self.ent_remetente.get().strip().lower()
        if rem and rem not in self.contas["fornecedores"]:
            self.contas["fornecedores"].append(rem)
            self.salvar_dados()
            self.atualizar_fornecedores_ui()
            self.ent_remetente.delete(0, 'end')
            self.log(f"Fornecedor {rem} adicionado à triagem.")

    def atualizar_contas_ui(self):
        self.contas_list.delete("1.0", "end")
        for c in self.contas["minhas_contas"]:
            self.contas_list.insert("end", f"✔️ {c['user']}\n")

    def atualizar_fornecedores_ui(self):
        self.forn_list.delete("1.0", "end")
        for r in self.contas["fornecedores"]:
            self.forn_list.insert("end", f"📧 {r}\n")

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_view.insert("end", f"[{ts}] {msg}\n")
        self.log_view.see("end")

    def toggle_engine(self):
        if not self.monitorando:
            self.monitorando = True
            self.btn_toggle.configure(text="PARAR TRIAGEM", fg_color="#e74c3c", hover_color="#c0392b")
            self.status_indicator.configure(text="● TriaBot Ativo", text_color="#2ecc71")
            self.log("🚀 Motor de triagem iniciado.")
            threading.Thread(target=self.main_loop, daemon=True).start()
        else:
            self.monitorando = False
            self.btn_toggle.configure(text="INICIAR TRIAGEM", fg_color="#2ecc71", hover_color="#27ae60")
            self.status_indicator.configure(text="● Bot em Espera", text_color="#e74c3c")
            self.log("🛑 Triagem interrompida.")

    def main_loop(self):
        while self.monitorando:
            for conta in self.contas["minhas_contas"]:
                if not self.monitorando: break
                self.processar_caixa(conta)
            if self.monitorando:
                time.sleep(60)

    def processar_caixa(self, conta):
        user = conta["user"]
        pw = SecurityManager.decrypt(conta["pass"])
        server = "imap.gmail.com" if "@gmail" in user else "outlook.office365.com"

        try:
            self.log(f"Triando e-mails de: {user}...")
            mail = imaplib.IMAP4_SSL(server)
            mail.login(user, pw)
            mail.select("inbox")
            _, data = mail.search(None, "UNSEEN")
            
            for num in data[0].split():
                _, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                from_ = email.utils.parseaddr(msg.get("From"))[1].lower()

                if from_ in self.contas["fornecedores"]:
                    self.triar_anexos(msg)
            mail.logout()
        except Exception as e:
            self.log(f"Erro na triagem de {user}: {str(e)}")

    def triar_anexos(self, msg):
        pasta_destino = "triagem_notas"
        os.makedirs(pasta_destino, exist_ok=True)
        for part in msg.walk():
            if "attachment" in str(part.get("Content-Disposition")):
                fn_bruto = part.get_filename()
                if fn_bruto:
                    dec = decode_header(fn_bruto)[0]
                    nome = dec[0].decode(dec[1] or 'utf-8') if isinstance(dec[0], bytes) else dec[0]
                    
                    if re.search(PADRAO_REGEX, nome.upper()):
                        caminho = os.path.join(pasta_destino, nome)
                        with open(caminho, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        self.log(f"✅ NF TRIADA: {nome}")

if __name__ == "__main__":
    App().mainloop()