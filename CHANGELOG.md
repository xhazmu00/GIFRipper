## 3.3 – střih pomocí tažných úchytů, Čas / Snímky

- Dvě skutečně tažná „pádla“ na časové ose, automatické změny OD/DO při tažení.
- Dvě nezávislé operace: odstranit označené snímky, nebo ponechat pouze výběr.
- Nová atomická editovací operace `GifProject.keep_range()` s jediným Undo/Redo.
- Přepínač Snímky / Čas přímo v inspektoru i časové ose; pole a vizualizace se
  aktualizují společně, bez ztráty výběru.
- Režim času používá původní individuální zpoždění GIF snímků a zobrazuje
  čas začátku a konce úseku. Hodnoty se zarovnávají na hranice snímků.
- Hodnoty času se potvrzují Enterem/opustěním vstupu, aby šly pohodlně napsat.
- Nahrávací a regionové backendy (Windows, GNOME Wayland, X11, IPC, FFmpeg)
  jsou shodné se stabilní verzí 3.2.
- Nové testy správného střihu včetně Undo/Redo, časových hranic, exportu,
  režimů osy a volitelného Qt GUI smoke testu.

## 3.2 – Nové fialové rozhraní (frontend only)

- Nové navigační menu: Nahrávání, Upravit GIF, Moje GIFy, Nastavení.
- Velké volby nahrávání a centrální tlačítko start podle referenčního návrhu.
- Střihová obrazovka s velkým náhledem, záložkami nástrojů a časovou osou.
- Tmavý/fialový a odpovídající světlý vzhled, nová fialová ikona.
- Automatické přepnutí na stránku editoru po otevření/nahrání GIFu.
- Přidané testy layoutu a kontroly otisků osmi backendových souborů.
- Bez úprav `capture_agent.py`, `capture_ipc.py`, `gnome_wayland.py`,
  `recording_flow.py`, `region_selector.py`, `recorder.py`, `editor.py`, `x11_capture.py`.

# GIFRipper 3.1 — živý průhledný výběr výseče Windows

- Oprava šedého pozadí: Windows výběr už nevykresluje uložený snímek z Qt ScreenCapture, který může být šedý nebo zastaralý. Místo toho používá skutečně průhledné bezrámečkové okno s `WA_TranslucentBackground` a `WA_NoSystemBackground`.
- Celá pracovní plocha je během výběru vidět živě. Mimo označení ji kryje pouze jemná poloprůhledná vrstva; uvnitř označení je plocha naprosto průhledná a ohraničená zeleně.
- Ovládání beze změny: klik, táhnout, pustit → automatické potvrzení, odpočet a nahrávání. Esc → zrušení.
- Nové regresní testy průhlednosti QPainter (spouští se, když je dostupné PySide6) a statické kontroly zapojení.
- Nahrávací backendy a GNU/Linux Wayland nejsou změněny. Ověření samotného okna na reálném Windows zůstává potřeba.

# GIFRipper 3.0 — dva režimy záznamu ve Windows

- Windows: dvě samostatná tlačítka „Nahrát celou obrazovku“ a „Nahrát výseč obrazovky“.
- Nahrávání celé plochy běží beze změny; výběr výseče otevře vlastní fullscreen screenshot overlay s tažením myši a automatickým potvrzením při puštění.
- Před pořízením náhledu se editor schová, takže výběr zobrazuje skutečnou pracovní plochu.
- Výběr regionu se mapuje na fyzické pixely téhož primárního monitoru, který používá Qt ScreenCapture; správně při různém DPI (100, 125, 150, 200 %).
- Esc výběr zruší; příliš malý region vyzve k opětovnému výběru.
- Žádný vnořený QDialog, žádná samostatná lišta tlačítek a žádné velké okraje.
- Ubuntu GNOME Wayland a ostatní nahrávací backendy zůstaly funkčně stejné.
- Nové automatické testy oblasti i UI propojení. Skutečné vykreslení a reálný záznam na Windows je potřeba ověřit na Windows.

# GIFRipper 2.9

- Windows, X11 a Qt/macOS: výběrové okno pro označení oblasti bylo vyřazeno z procesu nahrávání. Náhled se pouze použije k získání rozměrů obrazovky a automaticky následuje odpočet 3–2–1.
- Záznam se zahajuje přes plný obdélník `[0, 0, šířka, výška]` v pixelech backendu; správně reaguje na škálování Windows.
- Hlavní tlačítko je nyní označeno „Nahrát celou obrazovku“.
- Ubuntu GNOME Wayland a samotné nahrávací backendy byly zachovány beze změny.
- Výběr malé oblasti je dočasně vypnutý, dokud nebude bezpečně přepracován.
- Přidány regresní testy automatického startu a validace rozměrů obrazovky.

# GIFRipper 2.8

- Windows / X11 / Qt: výběrové okno nahrazeno bezrámečkovým fullscreen overlayem se screenshotem jako pozadím a kompaktní plovoucí lištou.
- Tlačítko **Celá obrazovka** nyní provádí skutečné potvrzení celého náhledu a po třech sekundách zahájí záznam (dříve jen mazalo výběr).
- Region je vizuálně označen 2px zeleným rámem se ztmavením okolí a uvedením rozměrů; klávesy Enter/Esc.
- Opraveno souřadnicové škálování 125%/150% DPI a možnost vybrat oblast začínající na (0, 0).
- GNOME Wayland backend, IPC kódování, nahrávání, zpracování GIFu a editor nebyly měněny.

# GIFRipper 2.7

- **Windows / české systémové kódování:** Opraveno čtení stavových zpráv z pomocného nahrávacího procesu. Textový stdout s `ensure_ascii=False` na Windows vytvářel nevalidní UTF-8 (`cp1250`), které hlavní okno odmítlo.
- JSON zprávy se nyní serializují do čistého ASCII (Unicode jako JSON escape) a přenášejí binárně; stejný formát používají příkazy rodiče.
- Regresní testy pokrývají české diakritické znaky, české cesty k souborům, rozdělení zpráv mezi více čtení a nucené kódování cp1250.
- Bez funkčních změn v Qt snímání, GNOME/Wayland, X11, editoru nebo vzhledu.

# GIFRipper 2.6

- OD/DO mají vodorovné a svislé odsazení, pole mají od sebe větší mezeru.
- FPS je zvýrazněné samostatně stylovaným číselným ovladačem se zelenou 2px linkou a jasným pozadím, v obou motivech.
- Odstraněny linuxové pokyny z panelu NAHRÁVÁNÍ (zůstávají v dokumentaci).
- Přepínač motivu přesunutý do pravé dolní části okna – oddělený od hlavních akcí. Ctrl+L a ukládání motivu zachováno.
- Nahrávací backendy, GIF střih, export, Undo/Redo beze změny.

# GIFRipper 2.5

- Výrazně zvýrazněna všechna tlačítka `STŘIH / EDITOR` – barevné výplně, **2px rámečky**, různé barvy pro jednotlivé typy akcí.
- Oddělené barvy pro značku OD (modrá) a DO (fialová), odstranění úseku (červená), rychlé střihy (oranžová), historii (zelená) a reset (neutrální).
- Stylování tlačítek a obou vstupních polí přímo na jednotlivých widgetech, aby jejich vzhled neztrácela `QScrollArea` / GNOME Qt téma.
- Vyladěn stav hover, stisknutí i zakázaných ovládacích prvků. Vše funguje v tmavém a světlém režimu.
- Záznam přes GNOME/Wayland, X11, Windows/macOS backend, střihové jádro a export GIFů **beze změny**.

# GIFRipper 2.4

- Nový přepínač tmavého / světlého motivu v horní liště, klávesová zkratka `Ctrl+L`.
- Trvalé ukládání zvoleného motivu přes `QSettings`.
- Vyšší kontrast tlačítek ve střižně, včetně neaktivních tlačítek před načtením GIFu.
- Sjednocení barev panelů, označovacích polí, titulku, časové osy, nahrávací lišty a výběru oblasti v obou motivech.
- **Nahrávání GNOME Wayland a export zůstávají nezměněné oproti funkční verzi 2.3.**

# GIFRipper 2.3

- Nová GNOME Wayland větev používá nativní systémový ScreenCast přes D-Bus, místo čekání na nepřicházející snímky Qt.
- Třísekundový odpočet před skutečným nahráváním.
- GNOME výchozí: záznam celé plochy, bez pauzy a bez výběru oblasti.
- Záznam přímo do dočasného WebM, převod do GIFu přes FFmpeg po zastavení.
- Nahrávací proces je izolovaný od GUI; při chybě ukáže konkrétní důvod.
- Původní Qt backend lze na Wayland GNOME vynutit pomocí GIFRIPPER_WAYLAND_BACKEND=qt.

# GIFRipper 2.2

- **Řešení „Kliknu na nahrávání a nic se neděje“:** stavová lišta zobrazuje, zda se spouští proces, čeká na oprávnění, čeká na první snímek nebo zahajuje záznam. Počítadlo sekund a zrušení čekání.
- **Linux X11:** samostatný spolehlivější backend `ffmpeg x11grab` pro náhled i živý obraz, s ověřeným záznamem, pauzou, dokončením a exportem.
- **Linux Wayland:** Qt ScreenCast/Portal zůstává samostatně. Pomocný proces explicitně používá nativní platformu Wayland (ne tichý fallback na XWayland). Pokud nemá Qt Wayland plugin nebo portal nevydává snímky, aplikace ukáže problém místo nekonečného čekání. **Tato větev nebyla prakticky otestována na reálném Wayland desktopu.**
- **Nahrávací proces:** před potvrzením reálného záznamu musí u X11 dorazit aspoň jeden živý snímek. V případě selhání zdroje přibyla diagnostika, odlišný timeout a informace o použitém backendu.
- **Qt frekvence:** zápis snímků do GIFu používá vybrané FPS a běží na časovači, ne na každém tiknutí UI.
- **Zachován editor** všech GIFů, střih, Undo/Redo, design i logo.

## Co se nezměnilo

Qt nahrávání na Waylandu je experimentální a závisí na konkrétním compositoru, portálu, PipeWire a dostupnosti Qt Wayland platform pluginu. Nová verze odhaluje selhání, ale nemůže garantovat zachycení obrazu na libovolném Waylandu. Doporučené dočasné řešení na Ubuntu, pokud Qt ScreenCast nefunguje, je relace **Ubuntu on Xorg** (výběr v přihlašovací obrazovce), nikoli přepnutí `DISPLAY` v terminálu.
