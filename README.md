# Assembly Proxy + Remote Menu · Free Fire iOS 1.132.10

**Layla build · made by @@prudenciodev**

## Direct Download

- **Full package (zip):** [Download ZIP](https://github.com/bts2019amo-ctrl/assembly-proxy-ios-remote-menu/raw/main/ASSEMBLY_PROXY_REMOTE_MENU_READY.zip)
- Repo archive: https://github.com/bts2019amo-ctrl/assembly-proxy-ios-remote-menu/archive/refs/heads/main.zip
- Or clone: `git clone https://github.com/bts2019amo-ctrl/assembly-proxy-ios-remote-menu.git`

## Status (resolvido)
- Assembly custom (74 IFix) servido pelo proxy na porta 7777
- Remote Menu web na porta 8080 com todos os toggles
- Estado sincronizado em remote_state.json + localConfig.json
- Features (ESP, Aimbot, etc.) existem no patch

## Como rodar
```bash
cd "SRC CODE ASSEMBLY PROXY"
py -m pip install -r requirements.txt
py run.py
```
ou `RUN_WINDOWS.bat`

- **7777** = proxy do assembly (iPhone)
- **8080** = Remote Menu → `http://SEU-IP:8080/`

## API
- `GET  /api/config`
- `POST /api/toggle`  body: `{"key":"esp","value":true}`

## Observação
O assembly chega no jogo. O painel remoto controla o estado salvo.
Controle 100% live (jogo ler o site no meio da partida) ainda requer IFix de poll adicional.

---
Layla · @@prudenciodev
