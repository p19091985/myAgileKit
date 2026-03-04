# myAgileKit

Coleção de ferramentas de produtividade e automação.

---

## 📁 Projetos

### 🎬 [youtube_multilang_downloader](./youtube_multilang_downloader/)

**Download de vídeos do YouTube com múltiplas faixas de áudio dublado e legendas embutidas.**

- ✅ Detecta automaticamente áudios dublados (PT, ES, FR, DE, JA, KO, etc.)
- ✅ Baixa múltiplas faixas de áudio em um único arquivo MKV
- ✅ Legendas embutidas (não em arquivos separados)
- ✅ Interface gráfica (Tkinter)
- ✅ Usa Deno para resolver desafios do YouTube

```bash
# Executar
.venv/bin/python youtube_multilang_downloader/youtube_multilang.py

# Teste
.venv/bin/python youtube_multilang_downloader/test_subs_generation.py --no-download
```

---

### 🛠️ [DevTools](./DevTools/)

**Launcher unificado com ferramentas de desenvolvimento Python.**

| Ferramenta | Descrição |
|------------|-----------|
| **Corretor Streamlit** | Refatora scripts Streamlit (deprecation warnings) |
| **File Modifier** | Modificação em massa de arquivos (30+ linguagens) |
| **Interface Limpador** | GUI para ferramentas de limpeza de código |
| **Juntar Arquivos** | Combina múltiplos arquivos em um só |
| **Removedor Docstrings** | Remove docstrings preservando SQL strings |
| **Limpar Citações** | CLI para limpar citações em textos |

```bash
# Executar launcher
.venv/bin/python DevTools/main.py
```

---

### 💻 [OSTools](./OSTools/)

**Scripts de automação para Windows.**

| Script | Descrição |
|--------|-----------|
| `windows-update-menu.bat` | Menu interativo para Windows Update |
| `windows-update-menu.ps1` | Versão PowerShell do menu |

---

## 🚀 Setup

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Linux/Mac)
source .venv/bin/activate

# Instalar dependências
pip install yt-dlp tkinter
```

## 📄 Licença

MIT