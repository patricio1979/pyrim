import os
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
import subprocess
import tempfile
import verovio

# --- HELPER FUNCTION: Render SVG string to PNG using resvg CLI ---
def render_svg_to_png(
    svginput: str,
    outpath: str,
    resvg_path: str,
    width: int,
    height: int
) -> bool:
    """
    Uses resvg CLI to render an SVG string to a PNG file at exact pixel dimensions.
    Returns True if successful, else False.
    """
    command = [
        resvg_path,
        "--background", "transparent",
        "-w", str(width),
        "-h", str(height),
        "--dpi", "300",
        "-",
        outpath,
    ]

    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        stdout, stderr = proc.communicate(input=svginput.encode('utf-8'))

        if proc.returncode == 0:
            return True
        else:
            print(f"❌ resvg failed with return code {proc.returncode}")
            output = stdout.decode('utf-8') if stdout else 'No output'
            print(f"Output: {output}")
            return False

    except Exception as e:
        print(f"❌ Exception running resvg: {e}")
        return False


# --- HELPER: Extract part by name or fall back to first ---
def extract_part_xml(xml_path: str, part_name: str = None):
    """
    If part_name is given, extract that part. Otherwise, return full score.
    Returns XML string.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"Failed to parse XML: {e}")

    # Handle namespace
    if '}' in root.tag:
        ns = {'mxl': root.tag.split('}')[0].strip('{')}
    else:
        ns = {}

    if not part_name:
        # Return full score
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # Find part by name
    part_list = root.find(".//part-list", ns)
    if part_list is None:
        raise ValueError("No <part-list> found.")

    target_score_part = None
    first_score_part = None

    for score_part in part_list.findall("score-part", ns):
        if first_score_part is None:
            first_score_part = score_part

        part_name_elem = score_part.find("part-name", ns)
        if part_name_elem is not None and part_name_elem.text and part_name_elem.text.strip().lower() == part_name.lower():
            target_score_part = score_part
            break

    if target_score_part is None:
        print(f"⚠️ Part name '{part_name}' not found. Falling back to first part.")
        target_score_part = first_score_part

    part_id = target_score_part.get("id")
    if not part_id:
        raise ValueError("Selected score-part has no 'id' attribute.")

    # Build new XML with only this part
    new_root = ET.Element(root.tag, root.attrib)
    for child in root:
        if child.tag == "part-list":
            new_pl = ET.SubElement(new_root, "part-list")
            new_pl.append(target_score_part)
        elif child.tag == "part" and child.get("id") == part_id:
            new_root.append(child)
        elif child.tag != "part":
            new_root.append(child)

    return ET.tostring(new_root, encoding='unicode', xml_declaration=True)

# --- Helper PyInstaller path ---
import sys
import os
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# >---- MAIN FUNCTION: Parse ink pixels using resvg-rendered PNGs ----<
def parse_pixels(score, mru_count, direc, part_id, resvg_path_num, output_image_path=None):
    """
    Args:
        score (str): Filename of the MusicXML file (e.g., 'piece.xml')
        mru_count (int): Number of MRUs (used to normalize ink)
        direc (str): Directory containing the score
        part_id (str, optional): Part name (e.g., "Piano"). If None, full score.
        output_image_path (str, optional): Path to save rendered image(s).
        resvg_path (str, optional): Path to resvg binary. Required.

    Returns:
        float: Average ink pixels per MRU
    """

    total_ink_pixels = 0
    local_path = os.path.abspath(os.getcwd())
    score_path = os.path.join(local_path, direc, score)

    # --- DEBUG: Print the OS argument you're receiving ---
    print(f"DEBUG: resvg_path_num = '{resvg_path_num}'")
    print(f"DEBUG: type(resvg_path_num) = {type(resvg_path_num)}")
    # ------------------------------------------------------

    # --- FIX: Get the correct path to the resvg binary ---
    match resvg_path_num.lower():
        case 'windows':
            resvg_path = resource_path("external_app/resvg.exe")
        case 'linux':
            resvg_path = resource_path("external_app/resvg_linux")
        case 'macos':
            resvg_path = resource_path("external_app/resvg_macos")
        case _:
            raise ValueError(f"Unsupported OS: {resvg_path_num}")

    # --- CRITICAL DEBUG: Print the resolved path and check if it exists ---
    print(f"DEBUG: Using resvg binary at: {resvg_path}")
    print(f"DEBUG: Does file exist? {os.path.exists(resvg_path)}")
    if not os.path.exists(resvg_path):
        raise FileNotFoundError(f"CRITICAL: resvg binary not found at {resvg_path}. Check PyInstaller --add-data flag.")
    # ----------------------------------------------------------------------

    # Extract part (or full score) → XML string
    xml_str = extract_part_xml(score_path, part_id)

    # Initialize Verovio
    tk = verovio.toolkit()
    if not tk.loadData(xml_str):
        raise RuntimeError("Verovio failed to load extracted MusicXML.")

    tk.setOptions({
        'header': 'none',
        'footer': 'none',
        'adjustPageWidth': True,
        'adjustPageHeight': True,
        'condenseNotLastSystem': True,
        'svgViewBox': True
    })

    num_pages = tk.getPageCount()
    saved_images = []

    for page_num in range(1, num_pages + 1):
        # Render SVG
        svg_str = tk.renderToSVG(page_num)

        # Parse SVG dimensions
        try:
            svg_root = ET.fromstring(svg_str)
            if '}' in svg_root.tag:
                ns_uri = svg_root.tag.split('}')[0].strip('{')
                ns = {'svg': ns_uri}
            else:
                ns = {}

            # Try width/height first
            width_attr = svg_root.get('width')
            height_attr = svg_root.get('height')

            if width_attr and height_attr:
                width = int(float(width_attr.rstrip('px')))
                height = int(float(height_attr.rstrip('px')))
            else:
                # Fallback: parse viewBox="0 0 W H"
                viewbox = svg_root.get('viewBox')
                if viewbox:
                    parts = viewbox.strip().split()
                    if len(parts) == 4:
                        width = int(float(parts[2]))  # W
                        height = int(float(parts[3]))  # H
                    else:
                        raise ValueError("Invalid viewBox format")
                else:
                    raise ValueError("No width/height or viewBox found")
                
        except Exception as e:
            print(f"⚠️ Could not parse SVG dimensions: {e}. Using 1200x1600 fallback.")
            width, height = 1200, 1600

        # Create temp PNG file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            tmp_png_path = tmpfile.name

        # Render SVG → PNG using resvg
        if not render_svg_to_png(svg_str, tmp_png_path, resvg_path, width, height):
            raise RuntimeError(f"Failed to render page {page_num} to PNG.")

        # Optionally save to user-specified path
        if output_image_path:
            if num_pages == 1:
                final_path = output_image_path
            else:
                name, ext = os.path.splitext(output_image_path)
                final_path = f"{name}_page{page_num}{ext}"
            os.rename(tmp_png_path, final_path)
            saved_images.append(final_path)
            png_path = final_path
        else:
            png_path = tmp_png_path

        # Analyze ink
        try:
            with Image.open(png_path) as img:
                img = img.convert("RGB")
                data = np.array(img)
                gray = 0.299 * data[:, :, 0] + 0.587 * data[:, :, 1] + 0.114 * data[:, :, 2]
                ink_pixels = np.sum(gray < 200)  # Dark pixels = ink
                total_ink_pixels += ink_pixels
        except Exception as e:
            print(f"⚠️ Failed to analyze ink for page {page_num}: {e}")

        # Clean up temp file if not saved
        if not output_image_path and os.path.exists(tmp_png_path):
            os.unlink(tmp_png_path)

    # Return average ink per MRU
    ink_amount = float(total_ink_pixels) / mru_count if mru_count > 0 else 0.0
    return ink_amount