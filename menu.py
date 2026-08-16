from machine import Pin, I2C
import mcp23017
import neopixel
import time
import random
from machine_i2c_lcd import I2cLcd

# Spielmodi importieren
from reaction_game import reaction_game
from simon_says import simon_game
from battleship import battleship_game

# Hardware Setup
i2c_mcp = I2C(0, scl=Pin(1), sda=Pin(0))
mcp1 = mcp23017.MCP23017(i2c_mcp, 0x20)
mcp2 = mcp23017.MCP23017(i2c_mcp, 0x21)

i2c_lcd = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
lcd1 = I2cLcd(i2c_lcd, 0x26, 2, 16)
lcd2 = I2cLcd(i2c_lcd, 0x27, 2, 16)

# Menü-Button auf GP14
menu_button = Pin(14, Pin.IN, Pin.PULL_UP)

num_leds = 25
leds = neopixel.NeoPixel(Pin(2), num_leds)

# Spielliste
GAMES = [
    {"name": "Battleship", "short": "Battleship", "id": "battleship"},
    {"name": "Simon Says", "short": "Simon Says", "id": "simon"},
    {"name": "Reaction Game", "short": "Reaction", "id": "reaction"}
]

# Menü-Zustand
current_menu_index = 0
menu_button_prev_state = 1
last_button_time = 0
DEBOUNCE_TIME = 0.2 
HOLD_TIME = 2.0

# Farben für Menü-Animationen
COLOR_MENU_ACTIVE = (0, 255, 0)
COLOR_MENU_INACTIVE = (50, 50, 50)
COLOR_MENU_BACKGROUND = (0, 0, 50) 

# LCD Hilfsfunktionen
def lcd_show_message(lcd, line1="", line2="", center=False):
    """Zeigt Nachricht auf LCD an"""
    lcd.clear()
    if center:
        line1 = line1.center(16)
        line2 = line2.center(16)
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:16])

def lcd_animate_scroll(lcd, text, line=0, speed=0.3):
    """Scrollt Text horizontal über das Display"""
    if len(text) <= 16:
        lcd.move_to(0, line)
        lcd.putstr(text.center(16))
        return
    
    padded_text = "    " + text + "    "
    for i in range(len(padded_text) - 15):
        lcd.move_to(0, line)
        lcd.putstr(padded_text[i:i+16])
        time.sleep(speed)

# Menü-Funktionen
def menu_led_animation(selected_index):
    """LED-Animation für Menü basierend auf ausgewähltem Spiel"""
    leds.fill(COLOR_MENU_BACKGROUND)
    
    if selected_index == 0:  # Battleship
        for i in range(0, 25, 2):
            leds[i] = COLOR_MENU_ACTIVE
    elif selected_index == 1:  # Simon Says
        center_positions = [12, 7, 11, 13, 17]
        for pos in center_positions:
            leds[pos] = COLOR_MENU_ACTIVE
    elif selected_index == 2:  # Reaction Game
        edge_positions = [0, 1, 2, 3, 4, 9, 14, 19, 24, 23, 22, 21, 20, 15, 10, 5]
        for pos in edge_positions:
            leds[pos] = COLOR_MENU_ACTIVE
    
    leds.write()

def show_menu():
    """Zeigt das Hauptmenü synchron auf beiden Displays"""
    current_game = GAMES[current_menu_index]
    
    menu_text_line1 = "SPIELAUSWAHL"
    menu_text_line2 = f"< {current_game['short']} >"
    
    lcd_show_message(lcd1, menu_text_line1, menu_text_line2, center=True)
    lcd_show_message(lcd2, menu_text_line1, menu_text_line2, center=True)
    
    menu_led_animation(current_menu_index)

def show_menu_instructions():
    """Zeigt Bedienungsanweisungen auf beiden Displays"""
    lcd_show_message(lcd1, "Kurz = Wechseln", "Halten = Start", center=True)
    lcd_show_message(lcd2, "Kurz = Wechseln", "Halten = Start", center=True)

def show_game_info(game_info):
    """Zeigt detaillierte Spielinformationen synchron auf beiden Displays"""
    lcd1.clear()
    lcd2.clear()
    
    lcd_show_message(lcd1, game_info['name'][:16], "Wird geladen...", center=True)
    lcd_show_message(lcd2, game_info['name'][:16], "Wird geladen...", center=True)
    
    # Farben definieren
    colors = [
        (255, 0, 0),    # Rot
        (0, 255, 0),    # Grün
        (0, 0, 255),    # Blau
        (255, 255, 0),  # Gelb
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Lila
    ]
    
    # Lade-Animation mit LEDs in zufälligen Farben
    leds.fill((0, 0, 0))
    for i in range(25):
        random_color = random.choice(colors)
        leds[i] = random_color
        leds.write()
        time.sleep(0.1)
    
    # Bereit-Nachricht auf beiden Displays
    lcd_show_message(lcd1, "Spiel bereit!", "Los gehts!", center=True)
    lcd_show_message(lcd2, "Spiel bereit!", "Los gehts!", center=True)
    time.sleep(1)

def wait_for_button_action():
    """Wartet auf Button-Aktion und unterscheidet zwischen kurz und lang"""
    global menu_button_prev_state, last_button_time
    
    # Warten bis Button gedrückt wird
    while menu_button.value() == 1:
        time.sleep(0.01)
    
    # Button wurde gedrückt - Zeit messen
    button_press_start = time.time()
    button_held = False
    progress_shown = False
    
    while menu_button.value() == 0:
        elapsed = time.time() - button_press_start
        
        # Zeigen des Fortschritt nach kurzer Zeit
        if elapsed > 0.5 and not progress_shown:
            progress_shown = True
            lcd_show_message(lcd1, "Spiel starten?", "Halten...", center=True)
            lcd_show_message(lcd2, "Spiel starten?", "Halten...", center=True)
        
        # Zeigen des visuellen Fortschritts
        if elapsed > 0.5:
            progress = min((elapsed - 0.5) / (HOLD_TIME - 0.5), 1.0)
            progress_bars = int(progress * 10)
            progress_text = "█" * progress_bars + "░" * (10 - progress_bars)
            
            lcd_show_message(lcd1, "Spiel starten?", progress_text, center=True)
            lcd_show_message(lcd2, "Spiel starten?", progress_text, center=True)
            
            # LED-Fortschritt
            led_progress = int(progress * 25)
            leds.fill((0, 0, 0))
            for i in range(led_progress):
                intensity = int((i / 25) * 255)
                leds[i] = (0, intensity, 0)
            leds.write()
        
        # Prüfen, ob Hold-Time erreicht wurde
        if elapsed >= HOLD_TIME:
            button_held = True
            # Bestätigung für Spielstart
            lcd_show_message(lcd1, "*** START! ***", "Spiel wird", center=True)
            lcd_show_message(lcd2, "*** START! ***", "geladen...", center=True)
            leds.fill((0, 255, 0))
            leds.write()
            time.sleep(0.5)
            break
        
        time.sleep(0.05)
    
    # Button wurde losgelassen
    button_press_duration = time.time() - button_press_start
    
    # Warten bis Button komplett losgelassen wurde
    while menu_button.value() == 0:
        time.sleep(0.01)
    
    # Kurze Pause nach Loslassen
    time.sleep(0.1)
    
    # Bestimme Aktion basierend auf Dauer
    if button_held and button_press_duration >= HOLD_TIME:
        return "start_game"
    elif button_press_duration < 0.5:  # Kurzer Druck
        return "next_menu"
    else:
        # Button wurde vor Hold-Time losgelassen
        return "cancelled"

def menu_loop():
    """Haupt-Menüschleife"""
    global current_menu_index
    
    # Willkommens-Animation auf beiden Displays
    lcd_show_message(lcd1, "WILLKOMMEN bei", "BtnDestruction", center=True)
    lcd_show_message(lcd2, "WILLKOMMEN bei", "BtnDestruction", center=True)
    
    # Willkommens-LED-Animation
    for i in range(3):
        leds.fill((255, 255, 255))
        leds.write()
        time.sleep(0.3)
        leds.fill((0, 0, 0))
        leds.write()
        time.sleep(0.3)
    
    time.sleep(1)
    
    show_menu_instructions()
    time.sleep(6)
    
    while True:
        show_menu()
        
        action = wait_for_button_action()
        
        if action == "next_menu":
            # Kurzer Druck - nächster SPielmodus
            current_menu_index = (current_menu_index + 1) % len(GAMES)
            
            # Kurze Bestätigung für Menüwechsel
            lcd_show_message(lcd1, "Wechsle zu...", "", center=True)
            lcd_show_message(lcd2, "Wechsle zu...", "", center=True)
            time.sleep(0.3)
            
        elif action == "start_game":
            # Langer Druck, Spiel starten
            selected_game = GAMES[current_menu_index]
            show_game_info(selected_game)
            return selected_game['id']
            
        elif action == "cancelled":
            # Button wurde losgelassen, zeigt Menü wieder
            lcd_show_message(lcd1, "Abgebrochen", "Zurueck zum Menu", center=True)
            lcd_show_message(lcd2, "Abgebrochen", "Zurueck zum Menu", center=True)
            time.sleep(1)


def main():
    """Hauptprogramm mit Menü-System"""
    print("ButtonDestruction gestartet!")
    
    while True:
        try:
            selected_game = menu_loop()
            
            # Starte das ausgewählte Spiel
            if selected_game == "battleship":
                battleship_game()
            elif selected_game == "simon":
                simon_game()
            elif selected_game == "reaction":
                reaction_game()
            
            # Nach Spiel zurück zum Menü
            leds.fill((0, 0, 0))
            leds.write()
            
        except KeyboardInterrupt:
            print("Programm beendet.")
            break
        except Exception as e:
            print(f"Fehler: {e}")
            lcd_show_message(lcd1, "FEHLER!", "Neustart...", center=True)
            lcd_show_message(lcd2, "Bitte warten", "", center=True)
            time.sleep(2)

if __name__ == "__main__":
    main()