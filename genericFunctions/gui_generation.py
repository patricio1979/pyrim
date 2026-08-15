import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk  # Necesario para cargar imágenes
import os

def gui():
    # Variables to store user choices
    selected_folder = [None]          # Folder path
    musical_instrument = ['']         # Instrument name
    selected_language = ['en']        # Default language: English
    only_rhythm_pitch = [False]       # Toggle state
    generate_regression = [False]     # NEW: Regression tree toggle
    default_bpm = ['']                # Default Quarter BPM
    tactus_level = ['']               # Tactus level

    # Translation dictionary
    translations = {
        'en': {
            'title': "score_complexity Application",
            'welcome': "Welcome!",
            'load_folder': "Load Folder",
            'no_folder': "No folder selected",
            'language': "Select Language:",
            'instrument': "Which instrument we measure?",
            'process': "Process",
            'toggle_rp': "Just evaluate Rhythm and Pitch classes",
            'toggle_regression': "Generate regression tree",
            'bpm_label': "Default Quarter BPM",
            'tactus_label': "Tactus level",
            'license': "MIT License\nCopyright (c) 2026 PyRIM"
        },
        'es': {
            'title': "Aplicación score_complexity",
            'welcome': "¡Bienvenido!",
            'load_folder': "Cargar Carpeta",
            'no_folder': "Ninguna carpeta seleccionada",
            'language': "Seleccionar Idioma:",
            'instrument': "¿Qué instrumento medimos?",
            'process': "Procesar",
            'toggle_rp': "Sólo evalúa las clases Ritmo y Altura",
            'toggle_regression': "Generar un árbol de regresión",
            'bpm_label': "BPM por defecto para el cuarto",
            'tactus_label': "Nivel de Tactus",
            'license': "Licencia MIT\nCopyright (c) 2026 PyRIM"
        }
    }

    # References to widgets that need updating
    labels = {}

    # Function to select folder
    def select_folder():
        folder = filedialog.askdirectory()
        if folder:
            selected_folder[0] = folder
            folder_var.set(folder)

    # Function to update ALL UI text based on language
    def update_language_ui():
        lang = selected_language[0]
        root.title(translations[lang]['title'])
        labels['welcome'].config(text=translations[lang]['welcome'])
        load_button.config(text=translations[lang]['load_folder'])
        labels['lang_label'].config(text=translations[lang]['language'])
        labels['instr_label'].config(text=translations[lang]['instrument'])
        labels['bpm_label'].config(text=translations[lang]['bpm_label'])
        labels['tactus_label'].config(text=translations[lang]['tactus_label'])
        process_button.config(text=translations[lang]['process'])
        toggle_rp_button.config(text=translations[lang]['toggle_rp'])
        toggle_regression_button.config(text=translations[lang]['toggle_regression'])
        license_label.config(text=translations[lang]['license'])
        
        # Update folder label if unchanged
        if folder_var.get() == translations['en']['no_folder'] or folder_var.get() == translations['es']['no_folder']:
            folder_var.set(translations[lang]['no_folder'])
        
        # Update Tactus dropdown options and preserve selection
        if 'tactus_dropdown' in labels:
            menu = root.nametowidget(labels['tactus_dropdown'].menuname)
            menu.delete(0, 'end')  # Clear old options

            new_options = labels['tactus_options_es'] if lang == 'es' else labels['tactus_options_en']
            current_value = labels['tactus_var'].get()

            # Map current selection to new language
            if lang == 'es':
                option_map = dict(zip(labels['tactus_options_en'], labels['tactus_options_es']))
            else:
                option_map = dict(zip(labels['tactus_options_es'], labels['tactus_options_en']))

            # Try to keep equivalent option selected
            if current_value in option_map:
                labels['tactus_var'].set(option_map[current_value])
            else:
                labels['tactus_var'].set(new_options[0])  # fallback

            # Add new options to menu
            for option in new_options:
                menu.add_command(label=option, command=tk._setit(labels['tactus_var'], option))

    # Function to set language to English
    def set_english():
        selected_language[0] = 'en'
        us_button.config(relief=tk.SUNKEN)
        es_button.config(relief=tk.RAISED)
        update_language_ui()

    # Function to set language to Spanish
    def set_spanish():
        selected_language[0] = 'es'
        es_button.config(relief=tk.SUNKEN)
        us_button.config(relief=tk.RAISED)
        update_language_ui()

    # Function to process and close GUI
    def process_and_close():
        musical_instrument[0] = instrument_entry.get().strip()
        bpm_value = bpm_entry.get().strip()
        if not bpm_value:
            bpm_value = "60"
            bpm_entry.delete(0, tk.END)
            bpm_entry.insert(0, "60")
        default_bpm[0] = bpm_entry.get().strip()
        full_text = labels['tactus_var'].get()
        tactus_level[0] = full_text.split('.')[0].strip()  # Returns "1", "2", or "3"
        only_rhythm_pitch[0] = toggle_rp_var.get()
        generate_regression[0] = toggle_regression_var.get()
        root.quit()
        root.destroy()

    # Create the main window
    root = tk.Tk()
    root.title(translations['en']['title'])
    root.configure(bg="#ffffff")

    # Set window size and center it
    window_width = 600
    window_height = 900  # Increased height for larger logo
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)

    # Define font sizes
    large_font = ("Arial", 28)
    medium_font = ("Arial", 18)
    small_font = ("Arial", 13)
    button_font = ("Arial", 20)
    license_font = ("Arial", 9)

    # --- TOP FRAME for Logo, Welcome, and License ---
    top_frame = tk.Frame(root, bg="#ffffff", height=180)  # Increased height for larger logo
    top_frame.pack(fill="x", pady=(5, 0))
    top_frame.pack_propagate(False)  # Keep fixed height

    # LEFT: Logo (DOUBLE size: 160px height)
    try:
        logo_path = os.path.join("imgs", "pyRIM_logo.png")
        if os.path.exists(logo_path):
            # Load original image
            original_image = Image.open(logo_path)
            
            # Get original dimensions
            orig_width, orig_height = original_image.size
            
            # Target height (DOUBLE: 160px)
            target_height = 160
            # Calculate width to maintain aspect ratio
            target_width = int((target_height / orig_height) * orig_width)
            
            # Resize image maintaining aspect ratio
            resized_image = original_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(resized_image)
            
            logo_label = tk.Label(top_frame, image=logo_photo, bg="#ffffff")
            logo_label.image = logo_photo  # Keep reference
            logo_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)
        else:
            # Fallback if image not found
            logo_label = tk.Label(top_frame, text="[Logo]", font=("Arial", 30), bg="#ffffff", fg="gray")
            logo_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)
    except Exception as e:
        # Fallback if any error loading image
        logo_label = tk.Label(top_frame, text="[Logo]", font=("Arial", 30), bg="#ffffff", fg="gray")
        logo_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)

    # CENTER: Welcome text (next to logo)
    welcome_label = tk.Label(
        top_frame,
        text=translations['en']['welcome'],
        font=large_font,
        bg="#ffffff",
        fg="#000000"
    )
    welcome_label.place(x=140, y=80)  # Ajusta x e y para posicionar exactamente
    labels['welcome'] = welcome_label

    # RIGHT: License text
    license_label = tk.Label(
        top_frame,
        text=translations['en']['license'],
        font=license_font,
        bg="#ffffff",
        fg="#666666",  # Gray color
        justify="right"
    )
    license_label.pack(side=tk.RIGHT, padx=(0, 15), pady=10)
    labels['license'] = license_label

    # --- MAIN CONTENT ---

    # Language selection
    lang_label = tk.Label(
        root,
        text=translations['en']['language'],
        font=medium_font,
        bg="#ffffff",
        fg="#000000"
    )
    lang_label.pack(pady=(10, 5))
    labels['lang_label'] = lang_label

    # Flag buttons
    lang_button_frame = tk.Frame(root, bg="#ffffff")
    lang_button_frame.pack(pady=5)

    us_button = tk.Button(
        lang_button_frame,
        text="🇺🇸",
        font=("Arial", 16),
        width=3,
        relief="flat",
        bd=1,
        highlightbackground="white",
        command=set_english
    )
    us_button.pack(side=tk.LEFT, padx=10)

    es_button = tk.Button(
        lang_button_frame,
        text="🇪🇸",
        font=("Arial", 16),
        width=3,
        relief="flat",
        bd=1,
        highlightbackground="white",
        command=set_spanish
    )
    es_button.pack(side=tk.LEFT, padx=10)

    # Load folder button
    load_button = tk.Button(
        root,
        text=translations['en']['load_folder'],
        command=select_folder,
        width=20,
        relief="flat",
        bd=2,
        highlightbackground="white",
        font=button_font
    )
    load_button.pack(pady=(20, 5), anchor="center")

    # Folder label
    folder_var = tk.StringVar(value=translations['en']['no_folder'])
    folder_label = tk.Label(
        root,
        textvariable=folder_var,
        fg="black",
        bg="#ffffff",
        font=small_font,
        wraplength=500,
        justify="center"
    )
    folder_label.pack(pady=(0, 10), anchor="center")

    # Instrument label
    instr_label = tk.Label(
        root,
        text=translations['en']['instrument'],
        font=medium_font,
        bg="#ffffff",
        fg="#000000"
    )
    instr_label.pack(pady=(8, 5))
    labels['instr_label'] = instr_label

    # Instrument entry
    instrument_entry = tk.Entry(
        root,
        width=20,
        font=("Arial", 20),
        bg="#f0f0f0",
        fg="black",
        justify="center"
    )
    instrument_entry.bind("<FocusIn>", lambda e: e.widget.config(bg="#ffffff"))
    instrument_entry.bind("<FocusOut>", lambda e: e.widget.config(bg="#f0f0f0"))
    instrument_entry.pack(pady=(0, 8), anchor="center")

    # --- BPM Label ---
    bpm_label = tk.Label(
        root,
        text=translations['en']['bpm_label'],
        font=medium_font,
        bg="#ffffff",
        fg="black"
    )
    bpm_label.pack(pady=(8, 5), anchor="center")
    labels['bpm_label'] = bpm_label

    # --- BPM Entry ---
    bpm_entry = tk.Entry(
        root,
        width=10,
        font=medium_font,
        bg="#f0f0f0",
        fg="black",
        justify="center"
    )
    bpm_entry.bind("<FocusIn>", lambda e: e.widget.config(bg="#ffffff"))
    bpm_entry.bind("<FocusOut>", lambda e: e.widget.config(bg="#f0f0f0"))
    bpm_entry.insert(0, "60")  # Default value
    bpm_entry.pack(pady=(0, 8), anchor="center")

    # --- Tactus Label ---
    tactus_label = tk.Label(
        root,
        text=translations['en']['tactus_label'],
        font=medium_font,
        bg="#ffffff",
        fg="black"
    )
    tactus_label.pack(pady=(8, 5), anchor="center")
    labels['tactus_label'] = tactus_label

    # Tactus dropdown
    tactus_var = tk.StringVar()
    tactus_options_en = [
        "1. Pulse, Beginners",
        "2. Accents, Intermediate",
        "3. Whole measure, Advanced"
    ]
    tactus_options_es = [
        "1. Pulso, Principiantes",
        "2. Acentos, Intermedios",
        "3. Compás completo, Avanzados"
    ]

    # Set default selection to option 1
    tactus_var.set(tactus_options_en[0])

    # Create dropdown with black text
    tactus_dropdown = tk.OptionMenu(root, tactus_var, *tactus_options_en)
    tactus_dropdown.config(font=small_font, bg="#f0f0f0", fg="black", width=40, anchor="center")
    tactus_dropdown.pack(pady=(0, 8), anchor="center")
    
    menu = root.nametowidget(tactus_dropdown.menuname)
    menu.config(fg="black")

    # Store references for dynamic language update
    labels['tactus_var'] = tactus_var
    labels['tactus_dropdown'] = tactus_dropdown
    labels['tactus_options_en'] = tactus_options_en
    labels['tactus_options_es'] = tactus_options_es

    # Toggle 1: Just evaluate Rhythm and Pitch classes
    toggle_rp_var = tk.BooleanVar(value=False)
    toggle_rp_button = tk.Checkbutton(
        root,
        text=translations['en']['toggle_rp'],
        variable=toggle_rp_var,
        font=small_font,
        bg="#ffffff",
        fg="black",
        justify="center",
        wraplength=500
    )
    toggle_rp_button.pack(pady=(8, 3), anchor="center")

    # Toggle 2: Generate regression tree
    toggle_regression_var = tk.BooleanVar(value=False)
    toggle_regression_button = tk.Checkbutton(
        root,
        text=translations['en']['toggle_regression'],
        variable=toggle_regression_var,
        font=small_font,
        bg="#ffffff",
        fg="black",
        justify="center",
        wraplength=500
    )
    toggle_regression_button.pack(pady=(3, 25), anchor="center")

    # Process button
    process_button = tk.Button(
        root,
        text=translations['en']['process'],
        command=process_and_close,
        width=15,
        relief="flat",
        bd=1,
        highlightbackground="white",
        font=button_font
    )
    process_button.pack(pady=(0, 30), anchor="center")

    # --- INITIALIZE UI ---
    update_language_ui()

    # Start GUI loop
    root.mainloop()

    # After GUI closes, return all values
    return (selected_language[0], selected_folder[0], musical_instrument[0], 
            default_bpm[0], tactus_level[0], only_rhythm_pitch[0], 
            generate_regression[0])


# Run standalone (for testing)
if __name__ == "__main__":
    language, folder, instrument, bpm, tactus, only_rp, regression = gui()
    if folder:
        print(f"Continuing with folder: {folder}")
    else:
        print("No folder was selected.")

    if instrument:
        print(f"Working with the instrument: {instrument}")
    else:
        print("No instrument was entered.")

    print(f"Language selected: {language.upper()}")
    print(f"Only Rhythm & Pitch mode: {only_rp}")
    print(f"Generate regression tree: {regression}")
    print(f"Default Quarter BPM: {bpm if bpm else 'Not set'}")
    print(f"Tactus level: {tactus if tactus else 'Not set'}")