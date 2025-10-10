import tkinter as tk
from tkinter import filedialog

def gui():
    # Variables to store user choices
    selected_folder = [None]          # Folder path
    musical_instrument = ['']         # Instrument name
    selected_language = ['en']        # Default language: English
    only_rhythm_pitch = [False]       # Toggle state
    default_bpm = ['']                # Default Quarter BPM
    tactus_level = ['']               # Tactus level
    selected_os = ['']                # Operating System (new)

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
            'toggle': "Just evaluate Rhythm and Pitch classes",
            'bpm_label': "Default Quarter BPM",
            'tactus_label': "Tactus level",
            'os_label': "Operating System:",           # NEW
            'windows': "Windows",                      # NEW
            'linux': "Linux",                          # NEW
            'macos': "MacOS"                           # NEW
        },
        'es': {
            'title': "Aplicación score_complexity",
            'welcome': "¡Bienvenido!",
            'load_folder': "Cargar Carpeta",
            'no_folder': "Ninguna carpeta seleccionada",
            'language': "Seleccionar Idioma:",
            'instrument': "¿Qué instrumento medimos?",
            'process': "Procesar",
            'toggle': "Sólo evalúa las clases Ritmo y Altura",
            'bpm_label': "BPM por defecto para el cuarto",
            'tactus_label': "Nivel de Tactus",
            'os_label': "Sistema Operativo:",          # NEW
            'windows': "Windows",                      # NEW
            'linux': "Linux",                          # NEW
            'macos': "MacOS"                           # NEW
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
        labels['bpm_label'].config(text=translations[lang]['bpm_label'])      # Update BPM label
        labels['tactus_label'].config(text=translations[lang]['tactus_label'])  # Update Tactus label
        labels['os_label'].config(text=translations[lang]['os_label'])        # Update OS label
        process_button.config(text=translations[lang]['process'])
        toggle_button.config(text=translations[lang]['toggle'])  # Update toggle label
        
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

        # Update OS dropdown options and preserve selection
        if 'os_dropdown' in labels:
            menu = root.nametowidget(labels['os_dropdown'].menuname)
            menu.delete(0, 'end')  # Clear old options

            new_os_options = [
                translations[lang]['windows'],
                translations[lang]['linux'],
                translations[lang]['macos']
            ]
            current_os = labels['os_var'].get()

            # Map current OS to new language
            os_map_en = {
                'Windows': translations[lang]['windows'],
                'Linux': translations[lang]['linux'],
                'MacOS': translations[lang]['macos']
            }
            os_map_es = {
                translations['es']['windows']: translations[lang]['windows'],
                translations['es']['linux']: translations[lang]['linux'],
                translations['es']['macos']: translations[lang]['macos']
            }

            option_map = os_map_en if lang == 'en' else os_map_es

            if current_os in option_map:
                labels['os_var'].set(option_map[current_os])
            else:
                labels['os_var'].set(new_os_options[0])  # fallback

            # Add new options to menu
            for option in new_os_options:
                menu.add_command(label=option, command=tk._setit(labels['os_var'], option))

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
        default_bpm[0] = bpm_entry.get().strip()     # Capture BPM
        # >>> SOLO CAMBIO AQUÍ: Extraemos el número del texto seleccionado <<<
        full_text = labels['tactus_var'].get()
        tactus_level[0] = full_text.split('.')[0].strip()  # Returns "1", "2", or "3"
        only_rhythm_pitch[0] = toggle_var.get()      # Capture toggle state
        selected_os[0] = labels['os_var'].get()      # Capture OS selection
        root.quit()
        root.destroy()

    # Create the main window
    root = tk.Tk()
    root.title(translations['en']['title'])
    root.configure(bg="#ffffff")

    # Set window size and center it
    window_width = 600
    window_height = 800
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)

    # Define font sizes
    large_font = ("Arial", 25)
    medium_font = ("Arial", 18)
    small_font = ("Arial", 13)

    # --- WIDGETS ---

    # Welcome label
    welcome_label = tk.Label(
        root,
        text=translations['en']['welcome'],
        font=large_font,
        bg="#ffffff",
        fg="#000000"
    )
    welcome_label.pack(pady=20)
    labels['welcome'] = welcome_label

    # Create a frame to hold language (left) and OS (right) side by side
    top_frame = tk.Frame(root, bg="#ffffff")
    top_frame.pack(pady=10)

    # LEFT SIDE: Language selection
    left_frame = tk.Frame(top_frame, bg="#ffffff")
    left_frame.pack(side=tk.LEFT, padx=20)

    lang_label = tk.Label(
        left_frame,
        text=translations['en']['language'],
        font=medium_font,
        bg="#ffffff",
        fg="#000000"
    )
    lang_label.pack(pady=5)
    labels['lang_label'] = lang_label

    # Flag buttons
    lang_button_frame = tk.Frame(left_frame, bg="#ffffff")
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

    # RIGHT SIDE: Operating System selection
    right_frame = tk.Frame(top_frame, bg="#ffffff")
    right_frame.pack(side=tk.RIGHT, padx=20)

    os_label = tk.Label(
        right_frame,
        text=translations['en']['os_label'],
        font=medium_font,
        bg="#ffffff",
        fg="#000000"
    )
    os_label.pack(pady=5)
    labels['os_label'] = os_label

    # OS Dropdown
    os_var = tk.StringVar()
    os_options_en = [
        translations['en']['windows'],
        translations['en']['linux'],
        translations['en']['macos']
    ]
    os_options_es = [
        translations['es']['windows'],
        translations['es']['linux'],
        translations['es']['macos']
    ]

    os_var.set(os_options_en[0])  # Default: Windows

    os_dropdown = tk.OptionMenu(right_frame, os_var, *os_options_en)
    os_dropdown.config(font=small_font, bg="#f0f0f0", fg="black", width=15, anchor="center")
    os_dropdown.pack(pady=5)

    menu = root.nametowidget(os_dropdown.menuname)
    menu.config(fg="black")

    # Store references for dynamic language update
    labels['os_var'] = os_var
    labels['os_dropdown'] = os_dropdown

    # Load folder button
    load_button = tk.Button(
        root,
        text=translations['en']['load_folder'],
        command=select_folder,
        width=20,
        relief="flat",
        bd=2,
        highlightbackground="white",
        font=large_font
    )
    load_button.pack(pady=(40, 5), anchor="center")

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
    folder_label.pack(pady=(0, 30), anchor="center")

    # Instrument label
    instr_label = tk.Label(
        root,
        text=translations['en']['instrument'],
        font=medium_font,
        bg="#ffffff",
        fg="#000000"
    )
    instr_label.pack(pady=(10, 5))
    labels['instr_label'] = instr_label

    # Instrument entry
    instrument_entry = tk.Entry(
        root,
        width=20,
        font=large_font,
        bg="#f0f0f0",
        fg="black",
        justify="center"
    )
    instrument_entry.bind("<FocusIn>", lambda e: e.widget.config(bg="#ffffff"))
    instrument_entry.bind("<FocusOut>", lambda e: e.widget.config(bg="#f0f0f0"))
    instrument_entry.pack(pady=(0, 20), anchor="center")

    # --- BPM Label ---
    bpm_label = tk.Label(
        root,
        text=translations['en']['bpm_label'],
        font=medium_font,
        bg="#ffffff",
        fg="black"
    )
    bpm_label.pack(pady=(10, 5), anchor="center")
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
    bpm_entry.pack(pady=(0, 20), anchor="center")

    # --- Tactus Label ---
    tactus_label = tk.Label(
        root,
        text=translations['en']['tactus_label'],
        font=medium_font,
        bg="#ffffff",
        fg="black"
    )
    tactus_label.pack(pady=(10, 5), anchor="center")
    labels['tactus_label'] = tactus_label

    # >>> SOLO CAMBIO AQUÍ: Reemplazamos Entry por OptionMenu <<<
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
    tactus_dropdown.pack(pady=(0, 20), anchor="center")
    
    menu = root.nametowidget(tactus_dropdown.menuname)
    menu.config(fg="black")

    # Store references for dynamic language update
    labels['tactus_var'] = tactus_var
    labels['tactus_dropdown'] = tactus_dropdown
    labels['tactus_options_en'] = tactus_options_en
    labels['tactus_options_es'] = tactus_options_es

    # Toggle: Just evaluate Rhythm and Pitch classes
    toggle_var = tk.BooleanVar(value=False)
    toggle_button = tk.Checkbutton(
        root,
        text=translations['en']['toggle'],
        variable=toggle_var,
        font=small_font,
        bg="#ffffff",
        fg="black",
        justify="center",
        wraplength=500
    )
    toggle_button.pack(pady=(10, 20), anchor="center")

    # Process button
    process_button = tk.Button(
        root,
        text=translations['en']['process'],
        command=process_and_close,
        width=20,
        relief="flat",
        bd=1,
        highlightbackground="white",
        font=large_font
    )
    process_button.pack(pady=50, anchor="center")

    # --- INITIALIZE UI ---
    update_language_ui()

    # Start GUI loop
    root.mainloop()

    # After GUI closes, return all values
    return selected_language[0], selected_folder[0], musical_instrument[0], default_bpm[0], tactus_level[0], only_rhythm_pitch[0], selected_os[0]


# Run standalone (for testing)
if __name__ == "__main__":
    language, folder, instrument, bpm, tactus, only_rp, os_selected = gui()
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
    print(f"Default Quarter BPM: {bpm if bpm else 'Not set'}")
    print(f"Tactus level: {tactus if tactus else 'Not set'}")
    print(f"Operating System: {os_selected if os_selected else 'Not set'}")