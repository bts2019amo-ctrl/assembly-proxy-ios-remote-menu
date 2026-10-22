# Assembly Proxy + Remote Menu · Free Fire iOS 1.132.10

**Layla build · made by @@prudenciodev**

## Direct Download

- **Full package (zip):** [Download ZIP](https://github.com/bts2019amo-ctrl/assembly-proxy-ios-remote-menu/archive/refs/heads/main.zip)
- Or clone: `git clone https://github.com/bts2019amo-ctrl/assembly-proxy-ios-remote-menu.git`

## O que é
- Proxy mitm que injeta `assembly-csharp-patch` custom (74 IFix)
- **Remote Menu** no navegador (porta 8080) com:
  - ESP · Aimbot · Arm · Team ESP · Crosshair
  - Jump Air / Control / Toggle · C-Arm · C-T1
- Controle remoto das opções via site + API

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

## Files
- `payload/` → assembly pronto (baixe o zip completo ou rode `build_assembly.py`)
- `source/` → original + BASE
- `run.py` → sobe tudo
- `assembly_proxy.py` → mitm + lógica

**Nota:** Features do BASE (`m_esp`, `m_aim` etc) já estão no assembly. O painel remoto controla o estado.

---
Layla · @@prudenciodev
