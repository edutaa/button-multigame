from machine import Pin, I2C
import mcp23017
import neopixel
import time
import random
from machine_i2c_lcd import I2cLcd

def simon_game():
    """Simon Says Game"""
    
    # I2C Setup für MCPs (Buttons und NeoPixel)
    i2c_mcp = I2C(0, scl=Pin(1), sda=Pin(0))
    mcp1 = mcp23017.MCP23017(i2c_mcp, 0x20)  # Spieler 1 Buttons
    mcp2 = mcp23017.MCP23017(i2c_mcp, 0x21)  # Spieler 2 Buttons

    num_leds = 25
    leds = neopixel.NeoPixel(Pin(2), num_leds)

    # I2C Setup für LCDs
    i2c_lcd = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
    lcd1 = I2cLcd(i2c_lcd, 0x26, 2, 16)  # Spieler 1 LCD
    lcd2 = I2cLcd(i2c_lcd, 0x27, 2, 16)  # Spieler 2 LCD

    # Menü-Button für Beenden
    menu_button = Pin(14, Pin.IN, Pin.PULL_UP)

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

    for pin in led_mapping_spieler1:
        mcp1[pin].input(pull=1)
    for pin in led_mapping_spieler2:
        mcp2[pin].input(pull=1)

    prev_state_sp1 = {pin: 1 for pin in led_mapping_spieler1}
    prev_state_sp2 = {pin: 1 for pin in led_mapping_spieler2}

    current_sequence = []
    sequence_colors = {}
    sequence_player = 0
    score_p1 = 0
    score_p2 = 0
    game_round = 1
    game_running = True

    # Erweiterte LCD Funktionen
    def lcd_show_message(lcd, line1="", line2="", center=False):
        """Zeigt Nachricht auf LCD an, optional zentriert"""
        lcd.clear()
        if center:
            line1 = line1.center(16)
            line2 = line2.center(16)
        lcd.move_to(0, 0)
        lcd.putstr(line1[:16])
        lcd.move_to(0, 1)
        lcd.putstr(line2[:16])

    def lcd_show_score():
        """Zeigt aktuellen Spielstand auf beiden LCDs"""
        lcd_show_message(lcd1, f"P1:{score_p1:2d} | P2:{score_p2:2d}", f"   Runde {game_round:2d}   ", center=True)
        lcd_show_message(lcd2, f"P1:{score_p1:2d} | P2:{score_p2:2d}", f"   Runde {game_round:2d}   ", center=True)

    def lcd_show_welcome():
        """Zeigt Willkommensnachricht"""
        lcd_show_message(lcd1, "  SIMON SAYS  ", "Spiel startet..", center=True)
        lcd_show_message(lcd2, "  SIMON SAYS  ", "Spiel startet..", center=True)
        time.sleep(2)

    def lcd_show_player_turn(player, action="erstellt"):
        """Zeigt an, welcher Spieler dran ist"""
        if action == "erstellt":
            msg1 = f"Spieler {player}"
            msg2 = "erstellt Sequenz"
        elif action == "zeigt":
            msg1 = f"Achtung P{3-player}!"
            msg2 = "Sequenz merken!"
        elif action == "wiederholt":
            msg1 = f"Spieler {player}"
            msg2 = "wiederholt jetzt"
        
        # Aktive Nachricht nur auf dem relevanten Display
        if player == 1:
            lcd_show_message(lcd1, msg1, msg2, center=True)
            lcd_show_message(lcd2, "Warte...", f"P{player} ist dran", center=True)
        else:
            lcd_show_message(lcd2, msg1, msg2, center=True)
            lcd_show_message(lcd1, "Warte...", f"P{player} ist dran", center=True)

    def lcd_show_countdown(seconds=3):
        """Zeigt Countdown auf beiden Displays"""
        for i in range(seconds, 0, -1):
            if menu_button.value() == 0:
                return False
            lcd_show_message(lcd1, "Start in...", f"     {i}     ", center=True)
            lcd_show_message(lcd2, "Start in...", f"     {i}     ", center=True)
            time.sleep(1)
        return True

    def lcd_show_sequence_progress(current, total, player):
        """Zeigt Fortschritt beim Sequenz eingeben"""
        progress = "=" * current + "-" * (total - current)
        lcd = lcd1 if player == 1 else lcd2
        lcd_show_message(lcd, f"Eingabe {current}/{total}", f"[{progress[:14]}]")

    def lcd_show_result(success, player):
        """Zeigt Ergebnis der Runde"""
        if success:
            lcd_show_message(lcd1, "  RICHTIG!  ", f"Punkt fuer P{player}", center=True)
            lcd_show_message(lcd2, "  RICHTIG!  ", f"Punkt fuer P{player}", center=True)
        else:
            lcd_show_message(lcd1, "   FALSCH!   ", f"P{player} verliert", center=True)
            lcd_show_message(lcd2, "   FALSCH!   ", f"P{player} verliert", center=True)

    def lcd_animate_text(text, delay=0.3):
        """Animiert Text auf beiden Displays"""
        spaces = " " * 16
        for i in range(len(text) + 16):
            if menu_button.value() == 0:
                return False
            display_text = (spaces + text + spaces)[i:i+16]
            lcd_show_message(lcd1, display_text, "", center=False)
            lcd_show_message(lcd2, display_text, "", center=False)
            time.sleep(delay)
        return True

    def show_exit_message():
        """Zeigt Beenden-Nachricht"""
        lcd_show_message(lcd1, f"Endstand P1:{score_p1}", f"P2:{score_p2} R:{game_round}", center=True)
        lcd_show_message(lcd2, f"Endstand P1:{score_p1}", f"P2:{score_p2} R:{game_round}", center=True)
        leds.fill((0, 0, 0))
        leds.write()
        time.sleep(2)

    # LEDs
    def clear_leds():
        leds.fill((0,0,0))
        leds.write()
        
    def get_random_color():
        """Gibt eine zufällige Farbe zurück"""
        colors = [
            (255, 0, 0),    # rot
            (0, 255, 0),    # grün
            (0, 0, 255),    # blau
            (255, 255, 0),  # gelb
            (255, 0, 255),  # magenta
            (0, 255, 255),  # cyan
            (255, 128, 0),  # orange
            (128, 0, 255),  # violett
            (255, 192, 203), # rosa
            (0, 128, 128),  # teal
        ]
        return random.choice(colors)

    def update_sequence_display():
        """Zeigt die aktuelle Sequenz mit den gespeicherten Farben"""
        clear_leds()
        if sequence_player == 1:
            mapping = led_mapping_spieler1
        else:
            mapping = led_mapping_spieler2
        
        for btn in current_sequence:
            if btn in mapping and btn in sequence_colors:
                leds[mapping[btn]] = sequence_colors[btn]
        leds.write()

    def light_led_temporarily(player, button_pin, color, duration=0.3):
        """Lässt einen Button mit spezifischer Farbe aufleuchten"""
        if player == 1:
            idx = led_mapping_spieler1[button_pin]
        else:
            idx = led_mapping_spieler2[button_pin]
        
        original_color = leds[idx]
        leds[idx] = color
        leds.write()
        time.sleep(duration)
        leds[idx] = original_color
        leds.write()

    def show_button_feedback(player, button_pin, correct=True):
        """Zeigt Feedback beim Nachtippen - grün bei richtig, rot bei falsch"""
        if player == 1:
            idx = led_mapping_spieler1[button_pin]
        else:
            idx = led_mapping_spieler2[button_pin]
        
        if correct:
            color = (0, 255, 0)  # Grün für richtig
        else:
            color = (255, 0, 0)  # Rot für falsch
        
        original_color = leds[idx]
        leds[idx] = color
        leds.write()
        time.sleep(0.4)
        leds[idx] = original_color
        leds.write()

    # --- Button Handling mit Menü-Check ---
    def wait_for_button_press(player, timeout=30):
        """Wartet auf Button-Druck mit Timeout und Menü-Check"""
        mcp = mcp1 if player == 1 else mcp2
        mapping = led_mapping_spieler1 if player == 1 else led_mapping_spieler2
        prev_state = prev_state_sp1 if player == 1 else prev_state_sp2
        
        start_time = time.time()
        
        while True:
            if menu_button.value() == 0:
                return "menu"
            
            if time.time() - start_time > timeout:
                return "timeout"
            
            for pin in mapping:
                val = mcp[pin].value()
                if prev_state[pin] == 1 and val == 0:
                    prev_state[pin] = val
                    return pin
                prev_state[pin] = val
            time.sleep(0.01)

    # Sequenz anzeigen 
    def show_sequence(sequence, player_to_show):
        """Zeigt die Sequenz mit den gleichen Farben wie bei der Erstellung"""
        lcd_show_player_turn(3-player_to_show, "zeigt")
        if not lcd_show_countdown(3):
            return False
        
        # Sequenz mit den gespeicherten Farben anzeigen
        for i, btn in enumerate(sequence):
            if menu_button.value() == 0:
                return False
            
            # Fortschritt anzeigen
            progress_lcd = lcd1 if player_to_show == 1 else lcd2
            lcd_show_message(progress_lcd, "Sequenz zeigen", f"Schritt {i+1}/{len(sequence)}")
            
            # LED mit der gespeicherten Farbe anzeigen
            if player_to_show == 1:
                idx = led_mapping_spieler1[btn]
            else:
                idx = led_mapping_spieler2[btn]
            
            # Verwenden der gespeicherten Farbe
            color = sequence_colors[btn]
            leds[idx] = color
            leds.write()
            time.sleep(0.4)
            leds[idx] = (0, 0, 0)
            leds.write()
            time.sleep(0.15)
        return True

    def get_sequence(player, length):
        """Lässt Spieler Sequenz eingeben mit Farbspeicherung"""
        nonlocal current_sequence, sequence_player, sequence_colors
        lcd_show_player_turn(player, "erstellt")
        time.sleep(1)
        
        current_sequence = []
        sequence_colors = {}
        sequence_player = player
        
        while len(current_sequence) < length:
            lcd_show_sequence_progress(len(current_sequence), length, player)
            btn = wait_for_button_press(player)
            
            if btn == "menu":
                return "menu"
            elif btn == "timeout":
                lcd_show_message(lcd1, "Zeit abgelaufen!", "Spiel beendet", center=True)  
                lcd_show_message(lcd2, "Zeit abgelaufen!", "Spiel beendet", center=True)
                time.sleep(2)
                return "timeout"
            
            # Zufällige Farbe für diesen Button generieren und speichern
            color = get_random_color()
            sequence_colors[btn] = color
            
            current_sequence.append(btn)
            update_sequence_display()
            light_led_temporarily(player, btn, color, 0.3)
            time.sleep(0.2)
        
        # Sequenz komplett
        lcd = lcd1 if player == 1 else lcd2
        lcd_show_message(lcd, "Sequenz fertig!", center=True)
        time.sleep(1)
        return current_sequence

    def repeat_sequence(player, sequence):
        """Lässt Spieler Sequenz wiederholen mit Feedback"""
        lcd_show_player_turn(player, "wiederholt")
        time.sleep(1)
        
        # Zeige die Sequenz mit den originalen Farben vor dem Nachtippen
        update_sequence_display()
        time.sleep(1)
        
        for i, expected_btn in enumerate(sequence):
            pressed_btn = wait_for_button_press(player)
            
            if pressed_btn == "menu":
                return "menu"
            elif pressed_btn == "timeout":
                return False
            
            # Feedback geben: grün wenn richtig, rot wenn falsch
            correct = (pressed_btn == expected_btn)
            show_button_feedback(player, pressed_btn, correct)
            
            # Fortschritt anzeigen NACH der Eingabe
            lcd = lcd1 if player == 1 else lcd2
            if correct and i < len(sequence) - 1:  # Nicht beim letzten Element
                lcd_show_message(lcd, f"Richtig! {i+1}/{len(sequence)}", "Naechste Taste...")
                time.sleep(0.5)
            elif not correct:
                lcd_show_message(lcd, "Falsch!", "Schade!", center=True)
                time.sleep(1)
                return False
            
            if not correct:
                return False
                
        return True

    def blink_red(times=3, delay=0.3):
        for _ in range(times):
            if menu_button.value() == 0:
                return
            leds.fill((255,0,0))
            leds.write()
            time.sleep(delay)
            clear_leds()
            time.sleep(delay)

    def show_success_animation():
        """Verbesserte Erfolgs-Animation"""
        leds.fill((0, 255, 0))
        leds.write()
        if not lcd_animate_text("*** RICHTIG! ***", 0.1):
            return
        time.sleep(0.5)
        clear_leds()

    def show_final_winner():
        """Zeigt Endsieger bei Spielende"""
        if score_p1 > score_p2:
            winner_text = "SPIELER 1 GEWINNT!"
            lcd_show_message(lcd1, "*** SIEGER! ***", f"Mit {score_p1} Punkten", center=True)
            lcd_show_message(lcd2, "Gut gespielt!", f"P1 gewinnt {score_p1}:{score_p2}", center=True)
            # Sieges-Animation für P1
            for i in range(3):
                for led_idx in led_mapping_spieler1.values():
                    leds[led_idx] = (0, 255, 0)
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
        elif score_p2 > score_p1:
            winner_text = "SPIELER 2 GEWINNT!"
            lcd_show_message(lcd2, "*** SIEGER! ***", f"Mit {score_p2} Punkten", center=True) 
            lcd_show_message(lcd1, "Gut gespielt!", f"P2 gewinnt {score_p2}:{score_p1}", center=True)
            # Sieges-Animation für P2
            for i in range(3):
                for led_idx in led_mapping_spieler2.values():
                    leds[led_idx] = (255, 0, 0)
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
        else:
            winner_text = "UNENTSCHIEDEN!"
            lcd_show_message(lcd1, "UNENTSCHIEDEN!", f"{score_p1}:{score_p2} Punkte", center=True)
            lcd_show_message(lcd2, "UNENTSCHIEDEN!", "Beide super!", center=True)
            # Unentschieden-Animation
            for i in range(3):
                leds.fill((255, 255, 0))
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
        
        time.sleep(3)

    # --- Hauptspiel Loop ---
    def main_game_loop():
        nonlocal score_p1, score_p2, game_round, game_running
        
        # Spiel starten
        print("Simon Says gestartet!")
        lcd_show_welcome()
        clear_leds() 
        
        round_length = 2
        current_player = 1
        responder = 2
        max_rounds = 5

        while game_running and game_round <= max_rounds:
            # Menü-Check
            if menu_button.value() == 0:
                break
                
            lcd_show_score()
            time.sleep(2)

            # Neue Runde ankündigen
            lcd_show_message(lcd1, f"=== RUNDE {game_round} ===", f"Laenge: {round_length}", center=True)
            lcd_show_message(lcd2, f"=== RUNDE {game_round} ===", f"Laenge: {round_length}", center=True)
            time.sleep(2)

            # Sequenz erstellen
            sequence = get_sequence(current_player, round_length)
            if sequence == "menu" or sequence == "timeout":
                break
            
            time.sleep(0.5)
            
            # Sequenz zeigen
            if not show_sequence(sequence, responder):
                break
            
            update_sequence_display()
            time.sleep(0.5)

            # Sequenz wiederholen
            success = repeat_sequence(responder, sequence)
            
            if success == "menu":
                break
            elif success:
                if responder == 1:
                    score_p1 += 1
                else:
                    score_p2 += 1
                
                lcd_show_result(True, responder)
                show_success_animation()
                round_length += 1
                game_round += 1
                clear_leds()
                time.sleep(2)
            else:
                lcd_show_result(False, responder)
                blink_red()
                
                # Spieler wechseln
                current_player, responder = responder, current_player
                round_length = 2
                game_round = 1
                current_sequence = []
                sequence_colors = {}
                clear_leds()
                time.sleep(3)
                
                # Neues Spiel ankündigen
                lcd_show_message(lcd1, "Neues Spiel!", f"P{current_player} faengt an", center=True)
                lcd_show_message(lcd2, "Neues Spiel!", f"P{current_player} faengt an", center=True)
                time.sleep(2)

        # Spiel beendet
        if game_round > max_rounds:
            show_final_winner()
        
        show_exit_message()
        print("Simon Says beendet!")

    # Spiel starten
    main_game_loop()


if __name__ == "__main__":
    simon_game()
