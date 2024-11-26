import keyboard

def debug_keypress(event):
    print(f"Detected key: {event.name}")

print("Press any key to see how it's detected. Press 'Ctrl+C' to stop.")
keyboard.hook(debug_keypress)  # Hook to print all keypress events
keyboard.wait("esc")  #