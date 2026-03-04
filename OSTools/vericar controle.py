import pygame
import sys
import math

# --- Constantes de Design (Look & Feel) ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# Paleta de Cores "Dark Aesthetics"
COLOR_BG = (25, 25, 30)  # Fundo Dark Grafite
COLOR_CONTROLLER = (15, 15, 15)  # Preto PS1 Black
COLOR_OUTLINE = (60, 60, 60)  # Contorno sutil
COLOR_BUTTON_OFF = (40, 40, 40)  # Botão inativo
COLOR_BUTTON_ON = (0, 255, 127)  # "Spring Green" - Alta visibilidade
COLOR_TEXT = (220, 220, 220)
COLOR_DEBUG_TEXT = (100, 255, 100)


class PSControllerTester:
    def __init__(self):
        """Inicializa a engine do Pygame e configurações de janela."""
        pygame.init()
        pygame.joystick.init()

        # Configuração de Display com Hardware Acceleration se possível
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Professional PS Controller Diagnostic Tool")
        self.clock = pygame.time.Clock()

        # Fontes
        self.font_title = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.font_debug = pygame.font.SysFont("Consolas", 14)
        self.font_label = pygame.font.SysFont("Arial", 12, bold=True)

        self.joystick = None
        self.controller_connected = False

        # Tenta conectar no início
        self.check_for_controllers()

    def check_for_controllers(self):
        """Gerencia conexão (Hot-plugging)."""
        if pygame.joystick.get_count() > 0 and not self.controller_connected:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.controller_connected = True
            print(f" [+] Controle Conectado: {self.joystick.get_name()}")
        elif pygame.joystick.get_count() == 0:
            self.controller_connected = False
            self.joystick = None

    def draw_smooth_circle(self, x, y, radius, color):
        """Desenha círculos com antialiasing (borda suave)."""
        pygame.draw.circle(self.screen, color, (int(x), int(y)), radius)
        # Opcional: Adicionar gfxdraw para suavização extra se necessário,
        # mas o draw.circle do Pygame 2+ já é muito bom.

    def draw_button(self, x, y, radius, label, is_pressed, shape="circle"):
        """Renderiza um botão genérico com estado ativo/inativo."""
        color = COLOR_BUTTON_ON if is_pressed else COLOR_BUTTON_OFF

        if shape == "circle":
            self.draw_smooth_circle(x, y, radius, color)
            pygame.draw.circle(self.screen, COLOR_OUTLINE, (int(x), int(y)), radius, 2)
        elif shape == "rect":
            rect = pygame.Rect(x - radius, y - radius // 2, radius * 2, radius)
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, COLOR_OUTLINE, rect, 2, border_radius=5)
        elif shape == "dpad":
            # Lógica específica para desenhar partes do D-PAD
            rect = pygame.Rect(x, y, radius, radius)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLOR_OUTLINE, rect, 1)

        # Desenha o Label (ID do botão)
        if label:
            text_surf = self.font_label.render(str(label), True, (0, 0, 0) if is_pressed else (150, 150, 150))
            text_rect = text_surf.get_rect(center=(x, y))
            self.screen.blit(text_surf, text_rect)

    def render_controller_visuals(self):
        """Desenha a representação artística do controle."""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50

        # 1. Corpo do Controle (Forma estilo "DualShock/PS1")
        # Esquerda
        self.draw_smooth_circle(cx - 120, cy, 70, COLOR_CONTROLLER)
        # Direita
        self.draw_smooth_circle(cx + 120, cy, 70, COLOR_CONTROLLER)
        # Centro (Retângulo de conexão)
        pygame.draw.rect(self.screen, COLOR_CONTROLLER, (cx - 120, cy - 50, 240, 100))
        # "Pernas" do controle (Grips)
        pygame.draw.polygon(self.screen, COLOR_CONTROLLER, [
            (cx - 120, cy), (cx - 180, cy + 120), (cx - 100, cy + 120), (cx - 60, cy + 50)
        ])
        pygame.draw.polygon(self.screen, COLOR_CONTROLLER, [
            (cx + 120, cy), (cx + 180, cy + 120), (cx + 100, cy + 120), (cx + 60, cy + 50)
        ])

        if not self.controller_connected:
            text = self.font_title.render("Aguardando Controle...", True, (255, 100, 100))
            self.screen.blit(text, (cx - text.get_width() // 2, cy))
            return

        # 2. Leitura de Inputs
        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]

        # Tenta ler o Hat (D-Pad). Se não existir, assume (0,0)
        hat_x, hat_y = (0, 0)
        if self.joystick.get_numhats() > 0:
            hat_x, hat_y = self.joystick.get_hat(0)

        # Eixos (Analógicos) - Controles PS1 antigos podem não ter, mas vamos prever
        axes = [0.0] * 4
        num_axes = self.joystick.get_numaxes()
        for i in range(min(num_axes, 4)):
            axes[i] = self.joystick.get_axis(i)

        # --- Mapeamento Visual (LAYOUT) ---

        # LADO ESQUERDO: D-PAD (Setas)
        dpad_cx, dpad_cy = cx - 120, cy - 20
        sz = 25
        # Cima (Hat Y=1)
        self.draw_button(dpad_cx, dpad_cy - sz, sz, "UP", hat_y == 1, "dpad")
        # Baixo (Hat Y=-1)
        self.draw_button(dpad_cx, dpad_cy + sz, sz, "DN", hat_y == -1, "dpad")
        # Esquerda (Hat X=-1)
        self.draw_button(dpad_cx - sz, dpad_cy, sz, "LT", hat_x == -1, "dpad")
        # Direita (Hat X=1)
        self.draw_button(dpad_cx + sz, dpad_cy, sz, "RT", hat_x == 1, "dpad")

        # LADO DIREITO: Botões de Face (0, 1, 2, 3 - Mapeamento genérico)
        # Nota: A ordem física muda por marca, então mostro o ID
        face_cx, face_cy = cx + 120, cy - 20
        dist = 35
        # Topo (Triângulo)
        self.draw_button(face_cx, face_cy - dist, 18, "3/Y", buttons[3] if len(buttons) > 3 else False)
        # Direita (Bolinha)
        self.draw_button(face_cx + dist, face_cy, 18, "1/B", buttons[1] if len(buttons) > 1 else False)
        # Baixo (Xis)
        self.draw_button(face_cx, face_cy + dist, 18, "2/A", buttons[2] if len(buttons) > 2 else False)
        # Esquerda (Quadrado)
        self.draw_button(face_cx - dist, face_cy, 18, "0/X", buttons[0] if len(buttons) > 0 else False)

        # CENTRO: Select e Start (Geralmente 8 e 9)
        self.draw_button(cx - 30, cy, 20, "Sel", buttons[8] if len(buttons) > 8 else False, "rect")
        self.draw_button(cx + 30, cy, 20, "Sta", buttons[9] if len(buttons) > 9 else False, "rect")

        # OMBROS (L1, R1, L2, R2) - Desenhados acima do corpo
        self.draw_button(cx - 120, cy - 90, 40, "L1", buttons[4] if len(buttons) > 4 else False, "rect")
        self.draw_button(cx + 120, cy - 90, 40, "R1", buttons[5] if len(buttons) > 5 else False, "rect")
        self.draw_button(cx - 120, cy - 120, 30, "L2", buttons[6] if len(buttons) > 6 else False, "rect")
        self.draw_button(cx + 120, cy - 120, 30, "R2", buttons[7] if len(buttons) > 7 else False, "rect")

        # ANALÓGICOS (Stick Visualizer)
        # Stick Esquerdo (Eixos 0 e 1)
        lx = cx - 70 + (axes[0] * 20)
        ly = cy + 60 + (axes[1] * 20)
        pygame.draw.circle(self.screen, (30, 30, 30), (cx - 70, cy + 60), 30)  # Base
        pygame.draw.circle(self.screen, COLOR_BUTTON_ON if (abs(axes[0]) > 0.1 or abs(axes[1]) > 0.1) else (80, 80, 80),
                           (int(lx), int(ly)), 20)

        # Stick Direito (Eixos 2 e 3 ou 3 e 4)
        if num_axes >= 4:
            rx = cx + 70 + (axes[2] * 20)
            ry = cy + 60 + (axes[3] * 20)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx + 70, cy + 60), 30)  # Base
            pygame.draw.circle(self.screen,
                               COLOR_BUTTON_ON if (abs(axes[2]) > 0.1 or abs(axes[3]) > 0.1) else (80, 80, 80),
                               (int(rx), int(ry)), 20)

    def render_debug_panel(self):
        """Painel lateral com dados brutos para o programador/usuário."""
        panel_x = 20
        y = 20

        title = self.font_title.render("Debug Info", True, COLOR_TEXT)
        self.screen.blit(title, (panel_x, y))
        y += 40

        if not self.controller_connected:
            return

        # Lista botões ativos
        active_buttons = []
        for i in range(self.joystick.get_numbuttons()):
            if self.joystick.get_button(i):
                active_buttons.append(str(i))

        info = [
            f"Nome: {self.joystick.get_name()}",
            f"Botões Ativos: {', '.join(active_buttons) if active_buttons else 'Nenhum'}",
            f"Eixos (Analógicos): {self.joystick.get_numaxes()}",
            f"Hats (D-Pad): {self.joystick.get_numhats()}"
        ]

        # Adiciona valores dos eixos
        for i in range(self.joystick.get_numaxes()):
            val = self.joystick.get_axis(i)
            info.append(f"Axis {i}: {val:.2f}")

        # Adiciona valor do Hat
        if self.joystick.get_numhats() > 0:
            info.append(f"Hat 0: {self.joystick.get_hat(0)}")

        for line in info:
            text = self.font_debug.render(line, True, COLOR_DEBUG_TEXT)
            self.screen.blit(text, (panel_x, y))
            y += 20

    def run(self):
        """Loop principal do jogo (Game Loop)."""
        running = True
        while running:
            # 1. Processamento de Eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Hot-plugging (Detecta se plugou ou desplugou durante o uso)
                if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
                    self.check_for_controllers()

            # 2. Atualização e Desenho
            self.screen.fill(COLOR_BG)

            self.render_controller_visuals()
            self.render_debug_panel()

            # 3. Flip e Tick
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = PSControllerTester()
    app.run()