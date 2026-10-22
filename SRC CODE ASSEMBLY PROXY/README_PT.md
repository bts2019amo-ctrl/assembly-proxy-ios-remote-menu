# Layla Assembly Proxy + Remote Menu
## Free Fire iOS 1.132.10

### O que tem aqui
- Assembly custom (74 IFix = 71 oficiais + 3 do BASE)
- Proxy mitm (porta 7777) que injeta o assembly
- Remote Menu Web (porta 8080) com ESP / Aimbot / Arm / TeamESP / Crosshair / Jump etc
- Controle remoto pelo navegador

### Como rodar (Windows)
1. Extrai a pasta
2. Abre CMD dentro da pasta
3. Roda:
```
py -m pip install -r requirements.txt
py run.py
```
ou só dá double-click em `RUN_WINDOWS.bat`

### Portas
- **7777** → Proxy do assembly (configure o iPhone pra usar esse proxy)
- **8080** → Site do Remote Menu  
  Abre no navegador: `http://IP-DO-SEU-PC:8080/`

### Opções do menu remoto
ESP · Aimbot · Arm · Team ESP · Crosshair · Jump Air · Jump Control · Jump Toggle · C-Arm · C-T1

### API
- GET  http://IP:8080/api/config
- POST http://IP:8080/api/toggle   (JSON: {"key":"esp","value":true})

### Arquivos importantes
- payload/assembly-csharp-patch.gz     → o que o jogo baixa
- remote_state.json                    → estado atual do menu
- config/localConfig.json              → espelha o estado
- source/                              → original + BASE

### Observação
O BASE já contém as features (ESP/Aimbot etc).  
O painel remoto controla o estado.  
Para reação 100% live no meio da partida (sem menu in-game), o próximo upgrade é um IFix de poll no /api/config.

made by @@prudenciodev · Layla
