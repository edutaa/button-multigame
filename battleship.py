from machine import Pin, I2C
import mcp23017
import neopixel
import time
from machine_i2c_lcd import I2cLcd

def battleship_game():
    """Hauptfunktion für das Battleship-Spiel"""
    
    # Setup I2C und MCPs
    i2c_mcp = I2C(0, scl=Pin(1), sda=Pin(0))
    mcp1 = mcp23017.MCP23017(i2c_mcp, 0x20)  # Spieler 1
    mcp2 = mcp23017.MCP23017(i2c_mcp, 0x21)  # Spieler 2

    # I2C Setup für LCDs
    i2c_lcd = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
    lcd1 = I2cLcd(i2c_lcd, 0x26, 2, 16)  # Spieler 1 LCD
    lcd2 = I2cLcd(i2c_lcd, 0x27, 2, 16)  # Spieler 2 LCD

    num_leds = 25
    leds = neopixel.NeoPixel(Pin(2), num_leds)

    # Button LED Mapping
    led_mapping_spieler1 = {
        11: 0, 10: 1, 9: 2, 8: 3,
        12: 4, 13: 5, 14: 6, 15: 7,
        4: 8, 5: 9, 6: 10, 7: 11
    }

    led_mapping_spieler2 = {
        7: 13, 6: 14, 5: 15, 4: 16,
        15: 17, 14: 18, 13: 19, 12: 20,
        8: 21, 9: 22, 10: 23, 11: 24
    }

    # Farben
    COLOR_SHIP = (0, 0, 255)       # Blau: Schiffe dauerhaft sichtbar
    COLOR_HIT = (0, 255, 0)        # Grün: Treffer
    COLOR_MISS = (255, 0, 0)       # Rot: Fehlversuch
    COLOR_CLEAR = (0, 0, 0)        # Ausgeschaltet

    # Pins als Input mit Pull-Up konfigurieren
    for pin in led_mapping_spieler1:
        mcp1[pin].input(pull=1)
    for pin in led_mapping_spieler2:
        mcp2[pin].input(pull=1)

    prev_state_sp1 = {pin: 1 for pin in led_mapping_spieler1}
    prev_state_sp2 = {pin: 1 for pin in led_mapping_spieler2}

    # Schiffe für jeden Spieler: speichert Button-Pins der platzierten Schiffe
    schiffe = {
        1: set(),  # Spieler 1 Schiffe Button-Pins
        2: set()   # Spieler 2 Schiffe Button-Pins
    }

    # Spiel-Statistiken
    treffer_count = {1: 0, 2: 0}
    schuesse_count = {1: 0, 2: 0}

    # Menü-Button für Rückkehr zum Hauptmenü
    menu_button = Pin(14, Pin.IN, Pin.PULL_UP)

    # === LCD Funktionen ===
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

    def lcd_show_welcome():
        """Zeigt Willkommensnachricht"""
        lcd_show_message(lcd1, "Battleship", "Spiel startet...", center=True)
        lcd_show_message(lcd2, "Battleship", "Spiel startet...", center=True)
        time.sleep(2)

    def lcd_show_ship_placement(player, current, total):
        """Zeigt Schiffplatzierungs-Status"""
        lcd = lcd1 if player == 1 else lcd2
        other_lcd = lcd2 if player == 1 else lcd1
        
        if current == 0:
            lcd_show_message(lcd, f"Spieler {player}", f"Bereit: {current}/{total}")
        else:
            lcd_show_message(lcd, f"Spieler {player}", f"Schiff {current}/{total}")
        lcd_show_message(other_lcd, "Warte...", f"P{player} platziert", center=True)

    def lcd_show_game_status():
        """Zeigt aktuellen Spielstatus auf beiden Displays"""
        p1_schiffe = len(schiffe[1])
        p2_schiffe = len(schiffe[2])
        
        lcd_show_message(lcd1, f"P1: {p1_schiffe} Schiffe", f"P2: {p2_schiffe} Schiffe")
        lcd_show_message(lcd2, f"P1: {p1_schiffe} Schiffe", f"P2: {p2_schiffe} Schiffe")

    def lcd_show_turn(angreifer):
        """Zeigt an, wer am Zug ist"""
        angreifer_lcd = lcd1 if angreifer == 1 else lcd2
        verteidiger_lcd = lcd2 if angreifer == 1 else lcd1
        
        lcd_show_message(angreifer_lcd, "Du bist dran!", "Ziel anvisieren", center=True)
        lcd_show_message(verteidiger_lcd, "Gegner zielt...", "Bereit machen!", center=True)

    def lcd_show_attack_result(angreifer, verteidiger, treffer, pin):
        """Zeigt Angriffsergebnis"""
        if treffer:
            # Treffer!
            angreifer_lcd = lcd1 if angreifer == 1 else lcd2
            verteidiger_lcd = lcd2 if angreifer == 1 else lcd1
            
            lcd_show_message(angreifer_lcd, "*** TREFFER! ***", "Volltreffer!", center=True)
            lcd_show_message(verteidiger_lcd, "Getroffen!", "Schiff versenkt", center=True)
        else:
            # Verfehlt!
            angreifer_lcd = lcd1 if angreifer == 1 else lcd2
            verteidiger_lcd = lcd2 if angreifer == 1 else lcd1
            
            lcd_show_message(angreifer_lcd, "Leider verfehlt", "Daneben!", center=True)
            lcd_show_message(verteidiger_lcd, "Verfehlt!", "Glueck gehabt!", center=True)

    def lcd_show_statistics(player):
        """Zeigt Spielstatistiken für einen Spieler"""
        lcd = lcd1 if player == 1 else lcd2
        if schuesse_count[player] > 0:
            trefferquote = int((treffer_count[player] / schuesse_count[player]) * 100)
            lcd_show_message(lcd, f"Treffer: {treffer_count[player]}/{schuesse_count[player]}", f"Quote: {trefferquote}%")
        else:
            lcd_show_message(lcd, "Noch keine", "Schuesse", center=True)

    def lcd_show_winner(gewinner, verlierer):
        """Zeigt Gewinner und Verlierer an"""
        gewinner_lcd = lcd1 if gewinner == 1 else lcd2
        verlierer_lcd = lcd2 if gewinner == 1 else lcd1
        
        lcd_show_message(gewinner_lcd, "*** GEWONNEN! ***", "Alle versenkt!", center=True)
        lcd_show_message(verlierer_lcd, "Verloren :(", "Naechste Runde!", center=True)

    def lcd_show_countdown(seconds=3):
        """Zeigt Countdown"""
        for i in range(seconds, 0, -1):
            lcd_show_message(lcd1, "Naechste Runde", f"Start in {i}...", center=True)
            lcd_show_message(lcd2, "Naechste Runde", f"Start in {i}...", center=True)
            time.sleep(1)

    def lcd_animate_text(text, duration=2):
        """Animiert Text über beide Displays"""
        spaces = " " * 16
        full_text = spaces + text + spaces
        steps = len(full_text) - 15
        delay = duration / steps
        
        for i in range(steps):
            display_text = full_text[i:i+16]
            lcd_show_message(lcd1, display_text, "")
            lcd_show_message(lcd2, display_text, "")
            time.sleep(delay)

    def check_menu_button():
        """Prüft ob Menü-Button gedrückt wurde für Rückkehr zum Hauptmenü"""
        return menu_button.value() == 0

    # Spiel-Logik
    def clear_leds():
        leds.fill(COLOR_CLEAR)
        leds.write()

    def update_leds():
        """Zeigt alle Schiffe beider Spieler gleichzeitig an."""
        leds.fill(COLOR_CLEAR)
        # Spieler 1 Schiffe
        for pin in schiffe[1]:
            idx = led_mapping_spieler1.get(pin)
            if idx is not None:
                leds[idx] = COLOR_SHIP
        # Spieler 2 Schiffe
        for pin in schiffe[2]:
            idx = led_mapping_spieler2.get(pin)
            if idx is not None:
                leds[idx] = COLOR_SHIP
        leds.write()

    def light_led(player, pin, color, duration=0.5):
        """Leuchtet kurz eine LED in einer Farbe auf und zeigt danach alle Schiffe wieder an."""
        mapping = led_mapping_spieler1 if player == 1 else led_mapping_spieler2
        idx = mapping.get(pin)
        if idx is None:
            return
        leds[idx] = color
        leds.write()
        time.sleep(duration)
        update_leds()

    def wait_for_button_press(player):
        mcp = mcp1 if player == 1 else mcp2
        mapping = led_mapping_spieler1 if player == 1 else led_mapping_spieler2
        prev_state = prev_state_sp1 if player == 1 else prev_state_sp2

        while True:
            # Prüfen auf Menü-Button für Rückkehr
            if check_menu_button():
                time.sleep(0.1)
                if check_menu_button():
                    lcd_show_message(lcd1, "Zurueck zum", "Hauptmenu...", center=True)
                    lcd_show_message(lcd2, "Zurueck zum", "Hauptmenu...", center=True)
                    time.sleep(1)
                    return "MENU_EXIT"
            
            for pin in mapping:
                val = mcp[pin].value()
                if prev_state[pin] == 1 and val == 0:
                    prev_state[pin] = val
                    return pin
                prev_state[pin] = val
            time.sleep(0.01)

    def platziere_schiffe(player, anzahl=3):
        """Schiffplatzierung mit LCD-Anzeigen"""
        schiffe[player].clear()
        lcd_show_message(lcd1, f"Spieler {player}", "platziert Schiffe", center=True)
        lcd_show_message(lcd2, f"Spieler {player}", "platziert Schiffe", center=True)
        time.sleep(1)
        
        update_leds()
        
        while len(schiffe[player]) < anzahl:
            bereits_platziert = len(schiffe[player])
            lcd_show_ship_placement(player, bereits_platziert, anzahl)
            
            btn = wait_for_button_press(player)
            if btn == "MENU_EXIT":
                return "MENU_EXIT"
        
            if btn in schiffe[player]:
                lcd = lcd1 if player == 1 else lcd2
                lcd_show_message(lcd, "Schon belegt!", "Anderen Platz!", center=True)
                time.sleep(1)
                continue
            
            schiffe[player].add(btn)
            update_leds()
            
           
            
            # Bestätigung nach erfolgreichem Platzieren
            gerade_platziert = len(schiffe[player])
            lcd = lcd1 if player == 1 else lcd2
            lcd_show_message(lcd, f"Schiff {gerade_platziert} gesetzt!", f"({gerade_platziert}/{anzahl})", center=True)
            time.sleep(0.5)
        
        # Platzierung abgeschlossen
        lcd = lcd1 if player == 1 else lcd2
        lcd_show_message(lcd, "Alle Schiffe gesetzt!", "Bereit zum Kampf", center=True)
        time.sleep(1)
        return "SUCCESS"

    def show_hit_feedback_angreifer(player, pin):
        light_led(player, pin, COLOR_HIT, duration=0.5)

    def show_miss_feedback_angreifer(player, pin):
        light_led(player, pin, COLOR_MISS, duration=0.5)

    def show_miss_feedback_verteidiger(verteidiger, pin_angriff):
        """Zeigt dem Verteidiger das Feedback für einen Fehlschuss durch kurzes Blinken in Rot."""
        mapping = led_mapping_spieler1 if verteidiger == 1 else led_mapping_spieler2
        idx = mapping.get(pin_angriff)
        if idx is not None:
            original_color = leds[idx]
            leds[idx] = COLOR_MISS
            leds.write()
            time.sleep(0.3)
            leds[idx] = original_color
            leds.write()

    def zeige_trefferfeedback(verteidiger, pin_treffer):
        # LED vom getroffenen Schiff beim Verteidiger ausmachen
        mapping = led_mapping_spieler1 if verteidiger == 1 else led_mapping_spieler2
        idx = mapping.get(pin_treffer)
        if idx is not None:
            leds[idx] = COLOR_CLEAR
            leds.write()
        schiffe[verteidiger].remove(pin_treffer)
        update_leds()

    def spielzug(spieler_angreifer, spieler_verteidiger):
        """Erweiterte Spielzug-Funktion mit LCD-Ausgaben"""
        lcd_show_turn(spieler_angreifer)
        time.sleep(1)
        
        btn = wait_for_button_press(spieler_angreifer)
        if btn == "MENU_EXIT":
            return "MENU_EXIT"
            
        schuesse_count[spieler_angreifer] += 1
        
        if btn in schiffe[spieler_verteidiger]:
            # Treffer!
            treffer_count[spieler_angreifer] += 1
            zeige_trefferfeedback(spieler_verteidiger, btn)
            show_hit_feedback_angreifer(spieler_angreifer, btn)
            lcd_show_attack_result(spieler_angreifer, spieler_verteidiger, True, btn)
            time.sleep(2)
            return True
        else:
            # Verfehlt!
            show_miss_feedback_angreifer(spieler_angreifer, btn)
            show_miss_feedback_verteidiger(spieler_verteidiger, btn)
            lcd_show_attack_result(spieler_angreifer, spieler_verteidiger, False, btn)
            time.sleep(2)
            return False

    def zeige_spielende_animation(gewinner, verlierer):
        """Erweiterte Spielende-Animation mit LCD-Ausgaben"""
        lcd_show_winner(gewinner, verlierer)
        
        # LED Animation
        clear_leds()
        gewinner_mapping = led_mapping_spieler1 if gewinner == 1 else led_mapping_spieler2
        for pin in gewinner_mapping:
            idx = gewinner_mapping[pin]
            leds[idx] = COLOR_HIT
        
        verlierer_mapping = led_mapping_spieler1 if verlierer == 1 else led_mapping_spieler2
        for pin in verlierer_mapping:
            idx = verlierer_mapping[pin]
            leds[idx] = COLOR_MISS
        
        leds.write()
        time.sleep(3)
        
        # Statistiken zeigen
        lcd_show_statistics(gewinner)
        time.sleep(2)
        lcd_show_statistics(verlierer)
        time.sleep(2)

    def reset_statistics():
        """Setzt Statistiken zurück"""
        nonlocal treffer_count, schuesse_count
        treffer_count = {1: 0, 2: 0}
        schuesse_count = {1: 0, 2: 0}

    def spiel_loop():
        """Hauptspiel-Schleife"""
        lcd_show_welcome()
        
        current_player = 1
        anderer_spieler = 2

        while True:
            # Neues Spiel vorbereiten
            reset_statistics()
            
            # Schiffe platzieren
            result = platziere_schiffe(current_player)
            if result == "MENU_EXIT":
                return  # Zurück zum Hauptmenü
            
            result = platziere_schiffe(anderer_spieler)
            if result == "MENU_EXIT":
                return  # Zurück zum Hauptmenü
            
            # Kampfphase starten
            lcd_animate_text("*** KAMPF BEGINNT! ***", 2)
            
            # Spielschleife
            aktueller_angreifer = current_player
            aktueller_verteidiger = anderer_spieler
            
            while True:
                lcd_show_game_status()
                time.sleep(1)
                
                getroffen = spielzug(aktueller_angreifer, aktueller_verteidiger)
                
                if getroffen == "MENU_EXIT":
                    return  # Zurück zum Hauptmenü

                if getroffen:
                    if len(schiffe[aktueller_verteidiger]) == 0:
                        # Spiel gewonnen!
                        zeige_spielende_animation(aktueller_angreifer, aktueller_verteidiger)
                        
                        # Nächstes Spiel vorbereiten
                        lcd_show_message(lcd1, "Button = Weiter", "Oben = Menu", center=True)
                        lcd_show_message(lcd2, "Button = Weiter", "Oben = Menu", center=True)
                        
                        # Warten auf Eingabe - entweder neue Runde oder Menü
                        waiting = True
                        while waiting:
                            if check_menu_button():
                                time.sleep(0.1)
                                if check_menu_button():
                                    return  # Zurück zum Hauptmenü
                            
                            # Prüfen auf beliebigen Spieler-Button für neue Runde
                            for pin in led_mapping_spieler1:
                                if mcp1[pin].value() == 0:
                                    waiting = False
                                    break
                            for pin in led_mapping_spieler2:
                                if mcp2[pin].value() == 0:
                                    waiting = False
                                    break
                            time.sleep(0.05)
                        
                        lcd_show_countdown(3)
                        schiffe[1].clear()
                        schiffe[2].clear()
                        
                        # Spieler für nächstes Spiel wechseln
                        current_player, anderer_spieler = anderer_spieler, current_player
                        break
                    else:
                        # Weiterspielen, gleicher Spieler darf nochmal
                        lcd_show_message(lcd1, "Treffer!", "Nochmal schiessen", center=True)
                        lcd_show_message(lcd2, "Treffer!", "Nochmal schiessen", center=True)
                        time.sleep(1)
                else:
                    # Spielerwechsel
                    aktueller_angreifer, aktueller_verteidiger = aktueller_verteidiger, aktueller_angreifer

                time.sleep(0.5)

    # Spiel starten
    try:
        spiel_loop()
    except Exception as e:
        print(f"Battleship Fehler: {e}")
        lcd_show_message(lcd1, "Spiel-Fehler!", "Zurueck zu Menu", center=True)
        lcd_show_message(lcd2, "Spiel-Fehler!", "Zurueck zu Menu", center=True)
        time.sleep(2)
    finally:
        clear_leds()