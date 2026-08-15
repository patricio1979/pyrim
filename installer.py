import PyInstaller.__main__
import sys
import os

# --- Detect the operating system ---
if sys.platform.startswith('darwin'):
    # macOS (Apple Silicon or Intel)
    icon_ext = 'icns'
    separator = ':'
elif sys.platform.startswith('win'):
    # Windows
    icon_ext = 'ico'
    separator = ';'
else:
    # Linux and others
    icon_ext = 'png'  # or omit --icon entirely for Linux
    separator = ':'

# --- Build the PyInstaller argument list ---
args = [
    'pyRIM.py',
    '--onedir',      # Create a single executable file
    '--windowed',     # Hide the console (use --console if your app needs terminal I/O)
]

# --- Add the icon (if it exists) ---
icon_path = f'./imgs/pyRIM_icon.{icon_ext}'
if os.path.exists(icon_path):
    args.append(f'--icon={icon_path}')

# --- Define the folders to bundle ---
# Format: (source_folder, destination_folder)
data_folders = [
    ('./textDefinitions', 'textDefinitions'),
    ('./imgs', 'imgs'),
    ('./PNG_temp_score_files', 'PNG_temp_score_files'),
    ('./external_app', 'external_app'),
    # Add the Verovio font data from your venv
    ('./venv/lib/python3.12/site-packages/verovio/data', 'verovio/data'),
    # Add your genericFunctions module folder
    ('./genericFunctions', 'genericFunctions'),
]

# --- Add the --add-data flags ---
for src, dest in data_folders:
    # Check if source exists to avoid PyInstaller errors
    if os.path.exists(src):
        args.append(f'--add-data={src}{separator}{dest}')
    else:
        print(f"Warning: Source path '{src}' does not exist. Skipping.")

# --- CRITICAL: Add hidden imports for sklearn and scipy ---
# These are the most common culprits causing the import errors you saw.
hidden_imports = [
    # For sklearn
    'sklearn.utils._typedefs',          # ✅ Replaces 'sklearn.neighbors.typedefs'
    'sklearn.tree._criterion',          # ✅ Replaces 'sklearn.tree._utils'
    'sklearn.utils._weight_vector',     # Often needed
    'sklearn.utils._openmp_helpers',    # For OpenMP support
    'sklearn.metrics._dist_metrics',    # For distance metrics

    # For scipy.optimize (HiGHS solver)
    'scipy.optimize._highs',            # ✅ Main HiGHS module
    'scipy.optimize._highs.cython',     # ✅ Replaces '_highs_constants' and '_highs_wrapper'
    'scipy.optimize._highs._highs',     # Sometimes needed

    # Other common scipy hidden imports
    'scipy.sparse.csgraph._validation',
    'scipy._lib.messagestream',
    'scipy.linalg._fblas',              # BLAS/LAPACK
    'scipy.linalg._flapack',
    'scipy.special._ufuncs_cxx',
]

for hi in hidden_imports:
    args.append(f'--hidden-import={hi}')

# --- Run PyInstaller ---
print("Running PyInstaller with args:")
print("\n".join(args))
PyInstaller.__main__.run(args)