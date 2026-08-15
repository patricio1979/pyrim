import os
import sys
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
import subprocess
import tempfile
import verovio


# ============================================================
# HELPER 1
# Render SVG string to PNG using resvg CLI
# ============================================================

def render_svg_to_png(
    svginput: str,
    outpath: str,
    resvg_path: str,
    width: int,
    height: int
) -> bool:
    """
    Uses resvg CLI to render an SVG string to a PNG file
    at exact pixel dimensions.

    Returns:
        True if successful, False otherwise.
    """

    command = [
        resvg_path,
        "--background", "transparent",
        "--width", str(width),
        "--height", str(height),
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

        stdout, _ = proc.communicate(
            input=svginput.encode("utf-8")
        )

        if proc.returncode == 0:
            return True

        print(
            f"❌ resvg failed with return code "
            f"{proc.returncode}"
        )

        output = (
            stdout.decode("utf-8")
            if stdout
            else "No output"
        )

        print(f"Output: {output}")

        return False

    except Exception as e:

        print(
            f"❌ Exception running resvg: {e}"
        )

        return False


# ============================================================
# HELPER 2
# Extract a specific MusicXML part
# ============================================================

def extract_part_xml(
    xml_path: str,
    part_name: str = None
):
    """
    Extract a specific MusicXML part.

    The requested part can be specified using:

        - part-name       e.g. "Piano"
        - instrument-name e.g. "Violin"
        - part ID         e.g. "P1"

    If part_name is None:
        the complete MusicXML document is returned.

    If the requested part is not found:
        the first available part is used.

    Returns:
        XML string containing the selected part.
    """

    # --------------------------------------------------------
    # Parse XML
    # --------------------------------------------------------

    try:

        tree = ET.parse(xml_path)
        root = tree.getroot()

    except Exception as e:

        raise RuntimeError(
            f"Failed to parse XML: {e}"
        )

    # --------------------------------------------------------
    # Handle XML namespace
    # --------------------------------------------------------

    if "}" in root.tag:

        ns_uri = root.tag.split("}")[0].strip("{")

        ns = {
            "mxl": ns_uri
        }

    else:

        ns = {}

    # --------------------------------------------------------
    # Namespace-independent helpers
    # --------------------------------------------------------

    def find_child(parent, tag):

        if ns:

            return parent.find(
                f"mxl:{tag}",
                ns
            )

        return parent.find(tag)

    def find_children(parent, tag):

        if ns:

            return parent.findall(
                f"mxl:{tag}",
                ns
            )

        return parent.findall(tag)

    def local_name(tag):

        return tag.split("}")[-1]

    # --------------------------------------------------------
    # If no part requested:
    # return complete score
    # --------------------------------------------------------

    if not part_name:

        return ET.tostring(
            root,
            encoding="unicode",
            xml_declaration=True
        )

    # --------------------------------------------------------
    # Find part-list
    # --------------------------------------------------------

    part_list = find_child(
        root,
        "part-list"
    )

    if part_list is None:

        raise ValueError(
            "No <part-list> found."
        )

    # --------------------------------------------------------
    # Gather available score-parts
    # --------------------------------------------------------

    available_parts = []

    for score_part in find_children(
        part_list,
        "score-part"
    ):

        # XML ID
        current_id = score_part.get(
            "id",
            ""
        )

        # --------------------------------------------
        # <part-name>
        # --------------------------------------------

        part_name_elem = find_child(
            score_part,
            "part-name"
        )

        if (
            part_name_elem is not None
            and part_name_elem.text
        ):

            current_part_name = (
                part_name_elem.text.strip()
            )

        else:

            current_part_name = ""

        # --------------------------------------------
        # <instrument-name>
        # --------------------------------------------

        current_instrument_name = ""

        score_instrument = find_child(
            score_part,
            "score-instrument"
        )

        if score_instrument is not None:

            instrument_name_elem = find_child(
                score_instrument,
                "instrument-name"
            )

            if (
                instrument_name_elem is not None
                and instrument_name_elem.text
            ):

                current_instrument_name = (
                    instrument_name_elem.text.strip()
                )

        # --------------------------------------------
        # Store structured information
        # --------------------------------------------

        available_parts.append(
            {
                "id": current_id,
                "part_name": current_part_name,
                "instrument_name": current_instrument_name,
                "element": score_part
            }
        )

    # --------------------------------------------------------
    # Check that parts actually exist
    # --------------------------------------------------------

    if not available_parts:

        raise ValueError(
            "No <score-part> elements found."
        )

    # --------------------------------------------------------
    # Search requested part
    # --------------------------------------------------------

    requested = (
        str(part_name)
        .strip()
        .lower()
    )

    target_part = None

    for part in available_parts:

        candidates = [
            part["id"],
            part["part_name"],
            part["instrument_name"]
        ]

        candidates = [
            str(value).strip().lower()
            for value in candidates
            if value
        ]

        if requested in candidates:

            target_part = part
            break

    # --------------------------------------------------------
    # Fallback if part was not found
    # --------------------------------------------------------

    if target_part is None:

        available_names = []

        for part in available_parts:

            display_name = (
                part["part_name"]
                or part["instrument_name"]
                or part["id"]
            )

            available_names.append(
                f'{part["id"]}: {display_name}'
            )

        print(
            f'⚠️ Part "{part_name}" was not found. '
            f'Available parts: {available_names}. '
            f'Falling back to the first part.'
        )

        target_part = available_parts[0]

    # --------------------------------------------------------
    # Get actual XML ID
    # --------------------------------------------------------

    selected_part_id = target_part["id"]

    # --------------------------------------------------------
    # Find corresponding <part id="...">
    # --------------------------------------------------------

    target_score_part = None

    for score_part in find_children(
        root,
        "part"
    ):

        if score_part.get("id") == selected_part_id:

            target_score_part = score_part
            break

    if target_score_part is None:

        raise ValueError(
            f'Could not find <part id="'
            f'{selected_part_id}"> in the MusicXML.'
        )

    # --------------------------------------------------------
    # Build a new XML document
    # --------------------------------------------------------

    new_root = ET.Element(
        root.tag,
        root.attrib
    )

    for child in root:

        tag = local_name(child.tag)

        # --------------------------------------------
        # part-list
        # --------------------------------------------

        if tag == "part-list":

            new_part_list = ET.SubElement(
                new_root,
                child.tag,
                child.attrib
            )

            new_part_list.append(
                target_part["element"]
            )

        # --------------------------------------------
        # part
        # --------------------------------------------

        elif tag == "part":

            if (
                child.get("id")
                == selected_part_id
            ):

                new_root.append(child)

        # --------------------------------------------
        # Other score-level elements
        # --------------------------------------------

        else:

            new_root.append(child)

    # --------------------------------------------------------
    # Return XML string
    # --------------------------------------------------------

    return ET.tostring(
        new_root,
        encoding="unicode",
        xml_declaration=True
    )


# ============================================================
# HELPER 3
# PyInstaller resource path
# ============================================================

def resource_path(relative_path):
    """
    Get absolute path to resource.

    Works both during development and
    when packaged with PyInstaller.
    """

    try:

        base_path = sys._MEIPASS

    except Exception:

        base_path = os.path.abspath(".")

    return os.path.join(
        base_path,
        relative_path
    )


# ============================================================
# MAIN FUNCTION
# ============================================================

def parse_pixels(
    score,
    mru_count,
    direc,
    part_name,
    resvg_path_num,
    output_image_path=None
):
    """
    Calculate ink amount from rendered MusicXML notation.

    The MusicXML is rendered by Verovio using a Letter-sized
    page (8500 x 11000 Verovio units).

    The SVG is then rasterized to 1275 x 1650 pixels,
    corresponding to a Letter page at 150 DPI.

    Returns:
        float:
            Average ink pixels per MRU.
    """

    # --------------------------------------------------------
    # Initial values
    # --------------------------------------------------------

    total_ink_pixels = 0

    local_path = os.path.abspath(
        os.getcwd()
    )

    score_path = os.path.join(
        local_path,
        direc,
        score
    )

    # --------------------------------------------------------
    # Determine resvg executable
    # --------------------------------------------------------

    match resvg_path_num.lower():

        case "windows":

            resvg_path = resource_path(
                "external_app/resvg.exe"
            )

        case "linux":

            resvg_path = resource_path(
                "external_app/resvg_linux"
            )

        case "macos":

            resvg_path = resource_path(
                "external_app/resvg_macos"
            )

        case _:

            raise ValueError(
                f"Unsupported OS: "
                f"{resvg_path_num}"
            )

    # --------------------------------------------------------
    # Extract selected part
    # --------------------------------------------------------

    xml_str = extract_part_xml(
        score_path,
        part_name
    )

    # --------------------------------------------------------
    # Initialize Verovio
    # --------------------------------------------------------

    tk = verovio.toolkit()

    if not tk.loadData(xml_str):

        raise RuntimeError(
            "Verovio failed to load "
            "extracted MusicXML."
        )

    # --------------------------------------------------------
    # Verovio options
    # --------------------------------------------------------

    tk.setOptions(
        {
            "header": "none",
            "footer": "none",

            # Letter page in Verovio units
            "pageWidth": 8500,
            "pageHeight": 11000,

            "adjustPageWidth": False,
            "adjustPageHeight": False,

            "condenseNotLastSystem": True,
            "svgViewBox": True
        }
    )

    # --------------------------------------------------------
    # Number of pages
    # --------------------------------------------------------

    num_pages = tk.getPageCount()

    saved_images = []

    # --------------------------------------------------------
    # Process every page
    # --------------------------------------------------------

    for page_num in range(
        1,
        num_pages + 1
    ):

        # --------------------------------------------
        # Render SVG
        # --------------------------------------------

        svg_str = tk.renderToSVG(
            page_num
        )

        # --------------------------------------------
        # Determine SVG dimensions
        # --------------------------------------------

        try:

            svg_root = ET.fromstring(
                svg_str
            )

            width_attr = svg_root.get(
                "width"
            )

            height_attr = svg_root.get(
                "height"
            )

            if (
                width_attr
                and height_attr
            ):

                svg_width = float(
                    width_attr.rstrip("px")
                )

                svg_height = float(
                    height_attr.rstrip("px")
                )

            else:

                # ------------------------------------
                # Fallback: viewBox
                # ------------------------------------

                viewbox = svg_root.get(
                    "viewBox"
                )

                if viewbox:

                    parts = (
                        viewbox
                        .strip()
                        .split()
                    )

                    if len(parts) == 4:

                        svg_width = float(parts[2])
                        svg_height = float(parts[3])

                    else:

                        raise ValueError(
                            "Invalid viewBox format."
                        )

                else:

                    raise ValueError(
                        "No width/height or "
                        "viewBox found."
                    )

        except Exception as e:

            print(
                f"⚠️ Could not parse SVG "
                f"dimensions: {e}."
            )

            svg_width = 8500
            svg_height = 11000

        # --------------------------------------------
        # Fixed rasterization resolution
        #
        # Letter = 8.5 x 11 inches
        # 150 DPI = 1275 x 1650 pixels
        # --------------------------------------------

        target_width = 1275

        target_height = round(
            target_width
            * svg_height
            / svg_width
        )

        width = target_width
        height = target_height

        # --------------------------------------------
        # Temporary PNG
        # --------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False
        ) as tmpfile:

            tmp_png_path = tmpfile.name

        # --------------------------------------------
        # Render SVG → PNG
        # --------------------------------------------

        success = render_svg_to_png(
            svg_str,
            tmp_png_path,
            resvg_path,
            width,
            height
        )

        if not success:

            raise RuntimeError(
                f"Failed to render page "
                f"{page_num} to PNG."
            )

        # --------------------------------------------
        # Optional save
        # --------------------------------------------

        if output_image_path:

            if num_pages == 1:

                final_path = (
                    output_image_path
                )

            else:

                name, ext = os.path.splitext(
                    output_image_path
                )

                final_path = (
                    f"{name}_page"
                    f"{page_num}{ext}"
                )

            # Make sure destination exists

            output_dir = os.path.dirname(
                os.path.abspath(final_path)
            )

            if output_dir:

                os.makedirs(
                    output_dir,
                    exist_ok=True
                )

            # Replace existing file if necessary

            if os.path.exists(final_path):

                os.remove(
                    final_path
                )

            os.rename(
                tmp_png_path,
                final_path
            )

            saved_images.append(
                final_path
            )

            png_path = final_path

        else:

            png_path = tmp_png_path

        # --------------------------------------------
        # Analyze ink
        # --------------------------------------------

        try:

            with Image.open(
                png_path
            ) as img:

                # ------------------------------------
                # Convert to RGB
                # ------------------------------------

                img = img.convert(
                    "RGB"
                )

                data = np.array(
                    img
                )

                # ------------------------------------
                # Convert RGB → grayscale
                # ------------------------------------

                gray = (
                    0.299 * data[:, :, 0]
                    + 0.587 * data[:, :, 1]
                    + 0.114 * data[:, :, 2]
                )

                # ------------------------------------
                # Dark pixels = ink
                # ------------------------------------

                ink_pixels = np.sum(
                    gray < 200
                )

                total_ink_pixels += (
                    ink_pixels
                )

        except Exception as e:

            print(
                f"⚠️ Failed to analyze "
                f"ink for page {page_num}: {e}"
            )

        # --------------------------------------------
        # Delete temporary file
        # --------------------------------------------

        if (
            not output_image_path
            and os.path.exists(
                tmp_png_path
            )
        ):

            os.unlink(
                tmp_png_path
            )

    # ========================================================
    # Average ink per MRU
    # ========================================================

    if mru_count > 0:

        ink_amount = (
            float(total_ink_pixels)
            / mru_count
        )

    else:

        ink_amount = 0.0

    return ink_amount