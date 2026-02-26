import sys
import pygame
from visualization import App

def run_test():
    app = App()
    app._start_tournament()
    app.state = "PODIUM"
    app.tourn_timer = 5.0 # Skip animations to reach results
    
    try:
        app._draw_podium(0.1)
        print("_draw_podium succeeded")
    except Exception as e:
        import traceback
        traceback.print_exc()

    app.state = "TOURN_RESULTS"
    try:
        app._draw_tourn_results()
        print("_draw_tourn_results succeeded")
    except Exception as e:
        import traceback
        traceback.print_exc()

run_test()
