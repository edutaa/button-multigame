from machine import Pin, I2C
from machine_i2c_lcd import I2cLcd
import mcp23017
import neopixel
import time
import random

def reaction_game():
    """Reaction Game"""
    
    # I2C Setup für MCPs
    i2c_mcp = I2C(0, scl=Pin(1), sda=Pin(0))
    mcp1 = mcp23017.MCP23017(i2c_mcp, 0x20) # Spieler 1
    mcp2 = mcp23017.MCP23017(i2c_mcp, 0x21) # Spieler 2
    
    # I2C Setup für LCDs
    i2c_lcd = I2C(1, scl=Pin(7), sda=Pin(6), freq=400000)
    lcd1 = I2cLcd(i2c_lcd, 0x26, 2, 16) # SPieler 1 LCD
    lcd2 = I2cLcd(i2c_lcd, 0x27, 2, 16) # Spieler 2 LCD
    
    # Neopixel Setup
    num_leds = 25
    leds = neopixel.NeoPixel(Pin(2), num_leds)
    
    # Menü-Button für Beenden
    menu_button = Pin(14, Pin.IN, Pin.PULL_UP)
    
    # Button-LED-Zuordnung
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
    
    # Punkte
    punkte_sp1 = 0
    punkte_sp2 = 0
    
    def clear_leds():
        leds.fill((0, 0, 0))
        leds.write()
    
    def light_button(player, button_pin):
        if player == 1:
            led_index = led_mapping_spieler1[button_pin]
            leds[led_index] = (0, 255, 0)
        else:
            led_index = led_mapping_spieler2[button_pin]
            leds[led_index] = (255, 0, 0)
    
    def show_targets(sp1_pin, sp2_pin):
        clear_leds()
        light_button(1, sp1_pin)
        light_button(2, sp2_pin)
        leds.write()
    
    def lcd_show_message(lcd, line1="", line2="", center=False):
        """Zeigt Nachricht auf LCD an mit optionaler Zentrierung"""
        lcd.clear()
        if center:
            line1 = line1.center(16)
            line2 = line2.center(16)
        lcd.move_to(0, 0)
        lcd.putstr(line1[:16])
        lcd.move_to(0, 1)
        lcd.putstr(line2[:16])
    
    def show_welcome_screen():
        """Zeigt Willkommensbildschirm"""
        clear_leds()
        # Spieler 1 Display
        lcd_show_message(lcd1, "*** PLAYER 1 ***", "Bereit zum Kampf?", center=True)
        # Spieler 2 Display  
        lcd_show_message(lcd2, "*** PLAYER 2 ***", "Bereit zum Kampf?", center=True)
        time.sleep(2)
        
        # Spielregeln anzeigen
        lcd_show_message(lcd1, "REACTION GAME", center=True)
        lcd_show_message(lcd2, "REACTION GAME", center=True)
        time.sleep(2)
        
        # Countdown zum Start
        for i in range(3, 0, -1):
            lcd_show_message(lcd1, "START IN...", f">>> {i} <<<", center=True)
            lcd_show_message(lcd2, "START IN...", f">>> {i} <<<", center=True)
            time.sleep(1)
        
        lcd_show_message(lcd1, "*** LOS! ***", center=True)
        lcd_show_message(lcd2, "*** LOS! ***", center=True)
        time.sleep(1)
    
    def update_score_display():
        """Aktualisiert die Punkteanzeige für beide Spieler"""
        # Spieler 1 Display - Grünes Design
        lcd1.clear()
        lcd1.move_to(0, 0)
        lcd1.putstr(f"P1: {punkte_sp1:2d} | P2: {punkte_sp2:2d}")
        lcd1.move_to(0, 1)
        if punkte_sp1 > punkte_sp2:
            lcd1.putstr(">>> FUEHRUNG! <<<")
        elif punkte_sp1 < punkte_sp2:
            lcd1.putstr("   Aufholen!    ")
        else:
            lcd1.putstr("  Gleichstand   ")
        
        # Spieler 2 Display - Rotes Design
        lcd2.clear()
        lcd2.move_to(0, 0)
        lcd2.putstr(f"P1: {punkte_sp1:2d} | P2: {punkte_sp2:2d}")
        lcd2.move_to(0, 1)
        if punkte_sp2 > punkte_sp1:
            lcd2.putstr(">>> FUEHRUNG! <<<")
        elif punkte_sp2 < punkte_sp1:
            lcd2.putstr("   Aufholen!    ")
        else:
            lcd2.putstr("  Gleichstand   ")
    
    def show_round_info(runde, max_runden):
        """Zeigt Rundeninformation"""
        # LEDs clearen bevor Rundeninfo angezeigt wird
        clear_leds()
        lcd_show_message(lcd1, f"=== RUNDE {runde} ===", f"von {max_runden} Runden", center=True)
        lcd_show_message(lcd2, f"=== RUNDE {runde} ===", f"von {max_runden} Runden", center=True)
        time.sleep(1.5)
    
    def show_round_winner(gewinner, grund="richtig"):
        """Zeigt Rundengewinner mit Grund"""
        if gewinner == 1:
            if grund == "richtig":
                lcd_show_message(lcd1, "*** PUNKT! ***", "Gut gemacht!", center=True)
                lcd_show_message(lcd2, "   Zu langsam   ", "Naechste Runde!", center=True)
            else:  # grund == "gegner_fehler"
                lcd_show_message(lcd1, "*** BONUS! ***", "Gegner-Fehler!", center=True)
                lcd_show_message(lcd2, "   FEHLER!   ", "Falscher Button!", center=True)
        else:
            if grund == "richtig":
                lcd_show_message(lcd1, "   Zu langsam   ", "Naechste Runde!", center=True)
                lcd_show_message(lcd2, "*** PUNKT! ***", "Gut gemacht!", center=True)
            else:  # grund == "gegner_fehler"
                lcd_show_message(lcd1, "   FEHLER!   ", "Falscher Button!", center=True)
                lcd_show_message(lcd2, "*** BONUS! ***", "Gegner-Fehler!", center=True)
        time.sleep(2)
    
    def show_countdown_to_next_round(seconds):
        """Zeigt Countdown zur nächsten Runde"""
        # LEDs clearen vor Countdown
        clear_leds()
        for i in range(seconds, 0, -1):
            lcd_show_message(lcd1, "Naechste Runde", f"in {i} Sekunden...", center=True)
            lcd_show_message(lcd2, "Naechste Runde", f"in {i} Sekunden...", center=True)
            time.sleep(1)
        
        lcd_show_message(lcd1, "BEREIT?", "Nur gruenes Licht!", center=True)
        lcd_show_message(lcd2, "BEREIT?", "Nur rotes Licht!", center=True)
        time.sleep(0.5)
    
    def show_final_results():
        """Zeigt Endergebnis mit Siegerehrung"""
        lcd1.clear()
        lcd2.clear()
        
        if punkte_sp1 > punkte_sp2:
            # Spieler 1 gewinnt
            lcd_show_message(lcd1, "*** SIEGER! ***", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            lcd_show_message(lcd2, "   Verloren!    ", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            
            # Sieges-Animation für Spieler 1
            for i in range(3):
                for led_idx in led_mapping_spieler1.values():
                    leds[led_idx] = (0, 255, 0)
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
                
        elif punkte_sp2 > punkte_sp1:
            # Spieler 2 gewinnt
            lcd_show_message(lcd1, "   Verloren!    ", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            lcd_show_message(lcd2, "*** SIEGER! ***", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            
            # Sieges-Animation für Spieler 2
            for i in range(3):
                for led_idx in led_mapping_spieler2.values():
                    leds[led_idx] = (255, 0, 0)
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
                
        else:
            # Unentschieden
            lcd_show_message(lcd1, "UNENTSCHIEDEN!", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            lcd_show_message(lcd2, "UNENTSCHIEDEN!", f"Score: {punkte_sp1}-{punkte_sp2}", center=True)
            
            # Unentschieden-Animation
            for i in range(3):
                leds.fill((255, 255, 0))
                leds.write()
                time.sleep(0.5)
                clear_leds()
                time.sleep(0.3)
        
        time.sleep(3)
        
        lcd_show_message(lcd1, "BYE!", center=True)
        lcd_show_message(lcd2, "BYE!", center=True)
        time.sleep(2)
    
    def show_exit_message():
        """Zeigt Beenden-Nachricht"""
        lcd_show_message(lcd1, "Spiel beendet!", "Zurueck zum Menu", center=True)
        lcd_show_message(lcd2, f"Endstand:", f"{punkte_sp1} : {punkte_sp2}", center=True)
        clear_leds()
        time.sleep(2)
    
    def show_wrong_button_effect(player):
        """Zeigt Fehler-Animation für falschen Button"""
        if player == 1:
            # Spieler 1 Fehler - Alle seine LEDs rot blinken
            for led_idx in led_mapping_spieler1.values():
                leds[led_idx] = (255, 0, 0)
        else:
            # Spieler 2 Fehler - Alle seine LEDs rot blinken
            for led_idx in led_mapping_spieler2.values():
                leds[led_idx] = (255, 0, 0)
        
        leds.write()
        time.sleep(0.3)
        clear_leds()
        time.sleep(0.2)
        
        # Nochmal blinken
        if player == 1:
            for led_idx in led_mapping_spieler1.values():
                leds[led_idx] = (255, 0, 0)
        else:
            for led_idx in led_mapping_spieler2.values():
                leds[led_idx] = (255, 0, 0)
        
        leds.write()
        time.sleep(0.3)
        clear_leds()
    
    def wait_for_winner(sp1_pin, sp2_pin):
        """Wartet auf Gewinner der Runde - mit Bestrafung für falsche Buttons"""
        # Zeige Anweisungen
        lcd_show_message(lcd1, "DRUECKE", "GRUENES LICHT!", center=True)
        lcd_show_message(lcd2, "DRUECKE", "ROTES LICHT!", center=True)
        
        while True:
            # Prüfe Menü-Button zum Beenden
            if menu_button.value() == 0:
                return "menu", "menu"
            
            # Prüfe Spieler 1 Buttons
            for pin in led_mapping_spieler1:
                val = mcp1[pin].value()
                if prev_state_sp1[pin] == 1 and val == 0:
                    prev_state_sp1[pin] = val
                    
                    if pin == sp1_pin:
                        # Richtiger Button von Spieler 1
                        return 1, "richtig"
                    else:
                        # Falscher Button von Spieler 1 - Spieler 2 bekommt Punkt
                        print(f"Spieler 1 drückte falschen Button: {pin} statt {sp1_pin}")
                        show_wrong_button_effect(1)
                        return 2, "gegner_fehler"
                else:
                    prev_state_sp1[pin] = val
            
            # Prüfe Spieler 2 Buttons
            for pin in led_mapping_spieler2:
                val = mcp2[pin].value()
                if prev_state_sp2[pin] == 1 and val == 0:
                    prev_state_sp2[pin] = val
                    
                    if pin == sp2_pin:
                        # Richtiger Button von Spieler 2
                        return 2, "richtig"
                    else:
                        # Falscher Button von Spieler 2 - Spieler 1 bekommt Punkt
                        print(f"Spieler 2 drückte falschen Button: {pin} statt {sp2_pin}")
                        show_wrong_button_effect(2)
                        return 1, "gegner_fehler"
                else:
                    prev_state_sp2[pin] = val
            
            time.sleep(0.01)
    
    # ==== Spiel starten ====
    print("Reaction Game gestartet!")
    show_welcome_screen()
    
    # ==== Haupt-Spielschleife ====
    runden = 0
    max_runden = 10
    
    while runden < max_runden:
        # Prüfe ob Menü-Button gedrückt wurde
        if menu_button.value() == 0:
            break
        
        # LEDs clearen am Anfang jeder Runde
        clear_leds()
        
        # Rundeninformation anzeigen
        show_round_info(runden + 1, max_runden)
        
        # Countdown vor Runde (außer bei erster Runde)
        if runden > 0:
            show_countdown_to_next_round(3)
        
        # LEDs nochmal clearen vor Ziel-Anzeige
        clear_leds()
        
        # Zufällige Buttons auswählen
        sp1_button = random.choice(list(led_mapping_spieler1.keys()))
        sp2_button = random.choice(list(led_mapping_spieler2.keys()))
        
        print(f"Runde {runden + 1}: Spieler 1 -> Pin {sp1_button}, Spieler 2 -> Pin {sp2_button}")
        
        # Ziele anzeigen
        show_targets(sp1_button, sp2_button)
        
        # Warte auf Gewinner
        gewinner, grund = wait_for_winner(sp1_button, sp2_button)
        
        # Prüfe ob Spiel beendet werden soll
        if gewinner == "menu":
            break
        
        clear_leds()
        
        # Punkte vergeben
        if gewinner == 1:
            if grund == "richtig":
                print("Spieler 1 gewinnt die Runde!")
            else:
                print("Spieler 1 bekommt Punkt durch Gegner-Fehler!")
            punkte_sp1 += 1
        else:
            if grund == "richtig":
                print("Spieler 2 gewinnt die Runde!")
            else:
                print("Spieler 2 bekommt Punkt durch Gegner-Fehler!")
            punkte_sp2 += 1
        
        # Alle LEDs des Gewinners aufleuchten lassen
        if gewinner == 1:
            leds.fill((0, 255, 0))  # Grün für Spieler 1
        else:
            leds.fill((255, 0, 0))  # Rot für Spieler 2
        leds.write()
        
        show_round_winner(gewinner, grund)
        
        clear_leds()
        
        update_score_display()
        time.sleep(2)
        
        runden += 1
    
    # Spiel beendet
    clear_leds()
    
    if runden >= max_runden:
        # Spiel normal beendet - Endergebnis anzeigen
        show_final_results()
    else:
        # Spiel durch Menü-Button beendet
        show_exit_message()
    
    print("Reaction Game beendet!")


if __name__ == "__main__":
    reaction_game()