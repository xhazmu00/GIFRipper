# GIFRipper 3.2 — fialové rozhraní podle vizuálního návrhu č. 2

**Vizuální aktualizace oproti 3.1.** Změnil se pouze frontend aplikace (příslušné části `app.py`, `modern_ui.py`, `modern_theme.py`, `widgets.py` a ikony). Všechny soubory pro zachytávání, výběr oblasti, střih a export jsou oproti 3.1 beze změny. Nové rozmístění i světelný/tmavý motiv byly inspirovány uživatelem dodanými referenčními obrázky.

- **Nahrávání:** vlevo vyber „Nahrávání“, zvol kartu „Nahrát celou obrazovku“ nebo na Windows „Nahrát výseč obrazovky“ a klikni na **Spustit nahrávání**. Na Ubuntu Wayland zůstává dostupný ověřený záznam celé plochy přes GNOME Shell.
- **Upravit GIF:** otevírání a export GIFu, náhled, ovládání po snímcích, časová osa a tři skutečné panely pro střih úseku, rychlý střih a historii změn.
- **Moje GIFy:** rychlý přístup k naposledy otevřenému GIFu a výběr libovolného souboru.
- **Nastavení:** světlý/tmavý režim a zkratky. Přepínání režimů také `Ctrl+L`.
- **Poznámka k návrhům:** některé graficky zobrazené funkce na vzorových obrázcích (prostorový crop, změna rozlišení, optimalizace, automatický délkový limit) nebyly součástí 3.1. Ve 3.2 nejsou vydávány za hotové funkce; jde o změnu vzhledu při zachování původního rozsahu funkcí.

## Spuštění

- **Windows:** `run_windows.bat`
- **Ubuntu:** `./run.sh`
- **macOS:** `./run_macos.command` (funkce zachytávání vyžadují oprávnění systému)

Nejdříve nainstaluj Python 3 a FFmpeg podle příslušné platformy. Při prvním spuštění spouštěč vytvoří prostředí `.venv` a nainstaluje závislosti. Opravdové grafické vykreslení je potřeba otestovat na cílové platformě; statické testy nenahrazují test GUI.

---

## Historie předchozích verzí

# 🎩 GIFRipper 3.1 — Capture / Frame Editor

Desktopový editor a rekordér GIFů inspirovaný LICEcap. Samostatná implementace, nikoli fork LICEcap.

**Novinka 3.1 – průhledný výběr výseče ve Windows:**

- Výběr je nyní **skutečně průhledné celoobrazovkové okno** nad živou pracovní plochou. Nevykresluje uložený screenshot, který mohl být z Qt šedý nebo zastaralý.
- Nevybraná část obrazovky je jen **lehce ztmavená** (27 %), označený obdélník zůstává **úplně průhledný** a je ohraničený zeleně.
- **Klikni, táhni a pusť** pro potvrzení; `Esc` výběr zruší. Žádné dialogy ani potvrzovací tlačítko.
- Screenshot z pomocného procesu nyní slouží pouze k určení velikosti nahrávaných pixelů (DPI); do průhledné vrstvy se nekreslí.
- GNOME/Wayland, Windows nahrávací backend, třísekundový odpočet i GIF editor zůstávají beze změny.
- **Omezení testování:** vzhled průhlednosti je potřeba ověřit na reálném Windows. Automatické testy kontrolují geometrii, průhlednost kreslicího algoritmu a přítomnost nastavení Qt vrstvy; v tomto prostředí není PySide6.

**Novinky 3.0 – dva způsoby nahrávání pro Windows:**

- **Nahrát celou obrazovku:** původní spolehlivá větev. Kliknutí → první snímek z Qt → odpočet 3–2–1 → záznam primárního monitoru. Žádné výběrové okno.
- **Nahrát výseč obrazovky:** nejdříve schová okno GIFRipperu a pořídí snímek primárního monitoru přes *stejný* Qt backend, který bude nahrávat. Potom otevře průhledný overlay nad živou plochou: **klikni a táhni levým tlačítkem myši, pusť → potvrdí se výběr → odpočet 3–2–1 → nahrávání výseče**.
- **Esc** zruší výběr bez záznamu. Pro malý výběr se ukáže upozornění a můžeš ho vybrat znovu (minimum 80 × 60 px).
- Žádné velké dialogové okno, žádný potvrzovací panel ani tlačítko „Celá obrazovka“ uvnitř výběru. Pracovní plocha je vidět živě pod průhlednou výběrovou vrstvou.
- Souřadnice výběru se přesně převádějí z Qt logických pixelů na fyzické pixely zachytávaného monitoru (testy pokrývají 100 %, 125 %, 150 % i 200% škálování).
- **Ubuntu GNOME Wayland:** nadále používá dosavadní funkční nativní GNOME rekordér, který nahrává celou plochu. **macOS/Linux:** mají zatím jedno tlačítko pro celou obrazovku. Windows má obě tlačítka.
- Výběr se týká primárního monitoru. Nahrávání jiné obrazovky nebo kombinace více monitorů zatím není součástí této verze.
- Během nahrávání může být plovoucí ovládací panel vidět v zaznamenaném výřezu, pokud leží uvnitř vybrané oblasti; lze jej odsunout mimo tuto oblast.
- **Ověření:** automatické testy střihu, backendů, překladu souřadnic a integrace obou tlačítek. Testy skutečného grafického okna na Windows vyžadují počítač s Windows; z tohoto prostředí to nešlo potvrdit.

**Historie 2.9 – nahrávání celé obrazovky:**

- Windows, X11 a Qt/macOS: výběrové okno bylo vyřazeno. Náhled poskytuje rozměry celé obrazovky a následuje odpočet 3–2–1.
- Windows full-screen režim je zachován jako samostatná volba.
- Ubuntu GNOME Wayland a nahrávací backendy zůstaly beze změny.

**Historie: 2.8 – původní pokus o výběr oblasti (ve 2.9 deaktivován):**

- **Bez velkého okna:** výběr oblasti nově zobrazuje screenshot přes celou plochu bez rámů a horní lišty. Ovládací prvky jsou v malém plovoucím panelu dole; už nepřekáží rozměrný dialog 980 × 660 px.
- **Celá obrazovka rovnou spustí záznam:** původní tlačítko jen mazalo výběr; nyní potvrdí celý náhled a pokračuje 3sekundovým odpočtem. Druhý klik na Začít není potřeba.
- **Výběr tažením myší:** přesný zelený rámeček a ztmavené okolí, popisek rozlišení, Enter = potvrdit, Esc = zrušit.
- **Oprava souřadnic a kraje:** převod souřadnic náhledu na skutečné pixely záznamu počítá s vysokým DPI/škálováním Windows (např. 125 %); funguje také výběr od levého horního rohu.
- **Ubuntu GNOME Wayland:** beze změn; dál se používá ověřená celoplošná větev GNOME Shell ScreenCast. Výběr regionu v této větvi zatím není implementován.
- Tento výběr už se ve verzi 2.9 neotevírá.

**Z verze 2.7 – oprava nahrávání na Windows:**


- Opraveno selhání „Nekompatibilní odpověď procesu záznamu: utf-8 codec can't decode byte…“ na Windows s českou lokalizací (např. cp1250).
- Pomocný proces nyní komunikuje s editorem přes binární pipe a ASCII-safe JSON s Unicode escape sekvencemi. České zprávy i cesty k souborům zůstávají beze ztráty.
- Změna se týká **jen komunikace procesu**; GNOME/Wayland, X11, samotné snímání ve Windows, UI a střih zůstávají beze změn.
- Pokud nahrávání na Windows selže po vyřešení kódování, další diagnostika už ukáže skutečný problém backendu.

**Z verze 2.6 – jemnější rozvržení editoru:**

- **OD / DO:** doplněny vnitřní a vnější mezery, takže číselná pole neleží těsně u okrajů posuvného panelu a mají mezeru i mezi sebou.
- **FPS:** ovladač snímkové frekvence nyní dostává přímo vlastní výraznou barevnou výplň, zelený 2px rámeček, stav hover a minimální šířku 112 px – v tmavém i světlém motivu.
- **Z panelu NAHRÁVÁNÍ odstraněn linuxový vysvětlující text.** Nastavení je neutrální pro všechny podporované systémy; návody jsou v README.
- **Přepínač světlého/tmavého motivu je v pravém dolním rohu** ve stavové liště, stranou od tlačítek Otevřít / Nahrát / Export. Zkratka `Ctrl+L` a uložení do nastavení fungují stejně.
- **Zachované nahrávání:** zdrojové soubory nahrávacích backendů a jejich řízení nebyly měněny.

**Z verze 2.5:**

- Všechna tlačítka panelu **STŘIH / EDITOR** mají přímo přiřazené barevné výplně a **2px barevné orámování** (i v neaktivním stavu). Na Linuxu s Waylandem tak nejsou odkázaná na dědění stylu přes Qt `QScrollArea`.
- Rozlišení akcí: **Nastavit OD = modrá**, **Nastavit DO = fialová**, **Vystřihnout úsek = červená**, **Rychlý střih = oranžová**, **Zpět / Znovu = zelená**, **Obnovit originál = neutrální**.
- Stejně barevně orámovaná jsou i pole **ZAČÁTEK / OD** a **KONEC / DO**. V obou motivech byla otestována čitelnost normálního i zakázaného stavu.
- GNOME Wayland nahrávání, 3sekundové odpočítávání, export a zpracování GIFů jsou **beze změny** oproti 2.4.

**Z verze 2.4 – vzhled a čitelnost:**

- V horní liště přibyl přepínač **☀ Světlý režim / ☾ Tmavý režim**. Alternativně `Ctrl+L`.
- Volba se automaticky uloží do uživatelského nastavení pomocí `QSettings` a zůstane i po restartu.
- Plnohodnotný světlý motiv se světlými plovoucími kartami, jemným pozadím a čitelnou časovou osou.
- Tlačítka sekce **STŘIH / EDITOR** mají vyšší kontrast v obou motivech. **Neaktivní tlačítka** jsou nyní také čitelná: aktivují se až po otevření GIFu nebo dokončení nahrávání.
- Záznamový backend GNOME Wayland a třísekundové odpočítávání z verze 2.3 zůstaly beze změny.

**Z předchozí verze 2.3 – Ubuntu / Wayland:**

- **3sekundový odpočet** po výběru oblasti (a na GNOME Wayland okamžitě po kliknutí na Nahrát).
- Na **Ubuntu GNOME + Wayland** aplikace standardně používá přímo `org.gnome.Shell.Screencast` (D-Bus), což obchází experimentální Qt/Wayland ScreenCapture, které na některých strojích nekonečně čekalo na první snímek.
- Přes GNOME se nahrává **celá obrazovka**, včetně případného nahrávacího ovládacího panelu; výběr konkrétní oblasti a pauza v této větvi zatím nejsou dostupné. Po zastavení se nativní WebM převede přes FFmpeg do GIFu a otevře ve střižně.
- **GNOME natívní backend není dostupný na KDE, Sway nebo jiném compositoru**. Tam se používá starší Qt/portal cesta; pokud bez povolení žádný obraz nepřijde, GIFRipper zobrazí chybu – samotný odpočet nemůže obejít zabezpečení Waylandu.
- Chyby spuštění GNOME rekordéru a exportu GIFu se zobrazí, aplikace zůstane ovladatelná.
- Pokud chceš starou Qt cestu v GNOME diagnosticky vyzkoušet, spusť `GIFRIPPER_WAYLAND_BACKEND=qt ./run.sh`.

**Dřívější vylepšení:**

1. **Samostatný proces nahrávání:** Qt/Wayland/desktop portal nyní běží odděleně od hlavního okna GIFRipperu. Pokud se systémový záznam zasekne nebo selže, hlavní editor zůstane použitelný a proces lze zrušit.
2. **Asynchronní komunikace s FFmpeg:** snímky se posílají z pomocného procesu přes omezenou frontu do samostatného zapisovacího vlákna. Pomalé kódování už neblokuje GUI.
3. **Opravený světlý panel:** inspektor/střih má explicitní tmavé pozadí včetně vnitřní plochy a scrollovacího viewportu, nezávisle na systémovém Qt tématu.
4. **Lepší chybové stavy:** systémový výběr obrazovky lze zrušit, nahrávání je hlídané časovým limitem a při chybách se zobrazí diagnostika potomka. V průběhu exportu lze ukončit zaseknutý pomocný proces.
5. **Zachovaný editor:** prohlížení snímků, přehrávání, označení OD/DO, mazání začátku/prostředku/konce, Undo/Redo, GIF export, časová osa s náhledy.

## Ubuntu / Linux

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg \
  xdg-desktop-portal xdg-desktop-portal-gnome pipewire wireplumber
```

Rozbal ZIP do vlastní složky (doporučeno **nedávat novou verzi přes starou**), potom:

```bash
cd GIFRipper-v3.1
chmod +x run.sh
./run.sh
```

`run.sh` automaticky vytvoří virtuální prostředí a stáhne Python závislosti. Pokud v systému chybí `python3-venv`, nainstaluj ho příkazem výše. Připojení k internetu je pro první instalaci PySide6 potřeba.

**Ubuntu GNOME Wayland (výchozí v 2.3):** Po stisku **Nahrát obrazovku** se zobrazí odpočet **3, 2, 1**. Program schová editor a pokusí se spustit nativní GNOME Shell ScreenCast přes D-Bus. Zaznamenává zatím **celou plochu**, bez výběru oblasti a bez pauzy. Po zastavení zvolíš cílový GIF, FFmpeg provede konverzi a výsledek se otevře v editoru. Systém při nahrávání zobrazuje vlastní indikátor. Na některých konfiguracích může GNOME D-Bus rekordér záznam odmítnout; v tom případě aplikace zobrazí konkrétní chybu. GNOME backend verze 2.3 byl úspěšně vyzkoušen na uživatelském Ubuntu s Waylandem. Na jiných konfiguracích fungování nelze garantovat.

**Ostatní Wayland / vynucené Qt:** Qt Multimedia ScreenCapture využívá XDG Desktop Portal + PipeWire. Nejprve je nezbytné systémové povolení, pak načtení prvního snímku a **3sekundový odpočet**. Funkce je v Qt experimentální a nemusí fungovat na každém desktopu.

**Linux X11:** Nově se používá FFmpeg `x11grab` v izolovaném procesu; tento backend byl ověřen pomocí Xvfb. Snímky se posílají do asynchronní fronty FFmpeg pro export.

## Windows 10/11

Potřebuješ nainstalovat Python 3.11+ (dostupný v `PATH`) a FFmpeg:

```powershell
winget install Gyan.FFmpeg
```

Otevři nové okno terminálu a spusť `run_windows.bat` nebo ho otevři poklepáním. Pro `.exe` na Windows:

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe build.py
```

Windows capture používá Qt ScreenCapture API. Build musí proběhnout na Windows; Python ZIP **není předkompilovaná aplikace**.

## macOS

Nainstaluj Python 3.11+ a FFmpeg (`brew install ffmpeg`), potom spusť `run_macos.command`. V macOS nastavení povol aplikaci nahrávání obrazovky. Pro `.app`:

```bash
.venv/bin/python -m pip install pyinstaller
.venv/bin/python build.py
```

Aplikace pro macOS je implementována, ale **na skutečném Macu nebyla otestována**; pro distribuci je navíc nutné zvážit podpis/notarizaci.

## Použití

- **GNOME Wayland:** **Nahrát obrazovku** → **3…2…1** → nahrávání celého monitoru/plochy → **Zastavit a uložit**.
- **X11, Windows, macOS, ostatní Qt:** **Nahrát celou obrazovku** → načtení snímku → **3…2…1** → nahrávání celé obrazovky. Žádné okno pro výběr oblasti se nezobrazí.
- Plovoucí lišta má **Pauza/Pokračovat** a **Zastavit a uložit**.
- **Otevřít GIF**, poté šipky ←/→ pro krokování snímků; mezerník pro přehrávání.
- **Označit OD/DO** pomocí spinboxů, tlačítek, Shift+klik a Alt+klik na časové ose. **Vystřihnout úsek** odstraní obě krajní snímky včetně obsahu mezi nimi.
- **Odstranit vše před snímkem / za snímkem** pro střih začátku a konce.
- **Ctrl+Z / Ctrl+Y** vrátí/znovu provede střih. **Ctrl+S** exportuje, originál zůstává beze změn.

### Když obrazovka opět nefunguje

Při kliknutí na nahrávání uvidíš v horní části **stavový pruh**, který říká, na co program čeká. Pokud backend nevrátí první snímek monitoru, automaticky zobrazí konkrétní chybu. Hlavní okno zůstává ovladatelné. Klikni na **× Zrušit čekání** nebo **× Zrušit dokončení**. Aplikace pomocný proces ukončí; při systémové chybě se pokusí zobrazit detail.

```bash
echo "$XDG_SESSION_TYPE"
./.venv/bin/python diagnose.py
```

Zkontroluj, zda běží portál a PipeWire:

```bash
systemctl --user status xdg-desktop-portal pipewire wireplumber
```

U jiného desktopu než GNOME může být místo `xdg-desktop-portal-gnome` nutný portál odpovídající tvému compositoru (KDE/wlroots). Nativní backend Qt bývá na Waylandu citlivý na grafické ovladače a GPU.

Pokud Qt FFmpeg backend nenachází, můžeš zkusit spustit s diagnostikou Qt:

```bash
QT_LOGGING_RULES='qt.multimedia.*=true' ./run.sh
```

Pomocný proces je teď oddělený **kvůli stabilitě UI**, ne jako zaručená oprava všech chyb platformního backendu.

## Výkon a časování

Nahrávání je ve výchozím stavu **12 FPS**, nastavit lze 1–30. FFmpeg dočasně ukládá bezeztrátové video, ze kterého po zastavení vytváří paletový GIF. Pro pomalý počítač/4K doporučujeme 8–12 FPS. Pokud je enkodér přetížený, fronta zahodí nadbytečné snímky místo zamrznutí; tím může být výsledná animace kratší než skutečný záznam. Aplikace počet vynechaných snímků ukazuje.

## Testy

```bash
python3 -m pytest -q
python3 -m compileall -q .
```

V prostředí vývoje prošlo **10 původních automatických testů** střihu, FFmpeg GIF exportu a neblokující fronty snímků. Qt GUI zde nebylo možné reálně vykreslit, protože PySide6 v testovacím prostředí není nainstalované a síťové stahování je nedostupné. Z toho důvodu **nemohu potvrdit funkčnost portálu na tvém Ubuntu, ani provést skutečné testy Windows/macOS**.

## Projekt

```text
app.py             Qt editor + neblokující řízení pomocného procesu (QProcess)
capture_agent.py   izolovaný Qt/portal/X11 worker, JSON IPC
x11_capture.py    ověřený FFmpeg X11 snímek a živé snímkování
recorder.py        FFmpeg + asynchronní fronta nahrávaných snímků
editor.py          střih GIFů / undo / redo / export
widgets.py         rozhraní, náhled, časová osa (nepoužívané staré widgety výběru oblasti zůstávají pro budoucí přepracování)
assets/            logo GIFRipper a ikony
bin/               místo pro volitelný lokální FFmpeg
run.sh             spuštění Linux
run_windows.bat    spuštění Windows
run_macos.command  spuštění macOS
build.py           PyInstaller pro cílový OS
tests/             unit & integrační testy
diagnose.py        diagnostika desktopového prostředí
```

GIFRipper aplikace samotná je MIT; PySide6, Pillow a FFmpeg mají vlastní licenční podmínky. Před redistribucí binárek je potřeba je ověřit.

## Pokud po kliknutí na Nahrát obrazovku nic nevidíš

Nově se ihned zobrazí zeleně orámovaný tmavý **stavový panel**. Ten ukazuje, zda již běží zachytávací proces, zda se čeká na systémové oprávnění a zda přicházejí skutečné snímky. Dokud není potvrzený začátek záznamu, tlačítko **Zrušit** aplikaci neblokuje.

Pokud používáš Ubuntu a systém nenabídne dialog sdílení obrazovky, zjisti session pomocí `echo "$XDG_SESSION_TYPE"`. V relaci X11 používá GIFRipper přímo FFmpeg `x11grab`; pokud je to Wayland, závisí nahrávání na systému Qt/Portal/PipeWire. Dokud nefunguje nativní Wayland screencast, bezpečná alternativa je přihlášení do **Ubuntu on Xorg** z přihlašovací obrazovky. Pouhé spuštění s `QT_QPA_PLATFORM=xcb` v aktuální Wayland relaci nedá přístup k celé obrazovce.

Pro výpis dostupných pluginů Qt a portálu spusť `.venv/bin/python diagnose.py`. Při hlášce o chybě Qt platform pluginu zkontroluj Qt Wayland knihovny a závislosti systému.

## Testy specifické pro 2.3

`python3 -m pytest -q` ověřuje střih, převod videa do GIFu a část logiky výběru backendu. **Nebylo možné spustit skutečný GNOME Shell/Wayland ani macOS/Windows zachytávání v testovacím prostředí.** Proto zatím nelze tvrdit, že nativní rekordér pracuje na každé verzi Ubuntu.

### Diagnostika nativního GNOME záznamu

```bash
./.venv/bin/python diagnose_wayland.py
```

Výpis ukáže, zda je k dispozici GNOME Shell ScreenCast D-Bus. Není pořízen žádný záznam. Pro **výslovně vyžádaný krátký záznam celé plochy** (pozor na soukromé údaje na obrazovce):

```bash
./.venv/bin/python diagnose_wayland.py --record
```

Po 3sekundovém odpočtu nahrává 3 sekundy a uloží `wayland-test.gif`. Pokud nahrávání selže, pošli výpis chyby. Bez souhlasu se žádná obrazovka nahrávat nebude.

### Test opravy Windows kódování

Z adresáře projektu: `python -m pytest tests/test_windows_ipc.py -q` (pro celou sadu `python -m pytest -q`). Test simuluje systémové kódování `cp1250`, běžné na českých Windows.

Nejjednodušší je rozbalit celý ZIP verze 3.1 do nové složky a spustit `run_windows.bat`. Pokud používáš GitHub, nejdřív nahraj změny verze 3.1 do svého repozitáře z Ubuntu (`git add .`, `git commit`, `git push`); teprve potom můžeš aktualizovat Windows příkazem `git pull`. **Nepřenášej samotný `capture_agent.py` bez nového souboru `capture_ipc.py`.**
