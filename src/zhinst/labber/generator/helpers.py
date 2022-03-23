import fnmatch
import re
import typing as t


def _replace_characters(s: str) -> str:
    """Replace characters that are not suitable to present in Labber.
 
    Returns:
        Labber compatible string.
    """
    if not s:
        return ""
    chars = [
        ("\n", " "),
        ("\r", ""),
        ('"', "`"),
        ("'", "`"),
        (";", ":"),
        ("%", " percent"),
    ]
    for c in chars:
        s = s.replace(c[0], c[1])
    return s

def _to_html_list(x: t.List[str]) -> str:
    """Convert list items to an HTML list.

    Returns:
        HTML list.
    """
    html_list = "<ul>"
    for item in x:
        item_cleaned = _replace_characters(item)
        html_list += f"<li>{item_cleaned}</li>"
    html_list += "</ul>"
    return html_list


def tooltip(
    desc: str, node: t.Optional[str] = None, enum: t.Optional[t.List[str]] = None
) -> str:
    """Convert tooltip arguments to HTML body.

    Args:
        desc: Paragraph
        node: Bolded text part.
        enum: List of strings to be converted to an HTML list.

    Returns:
        HTML body with given arguments
    """
    if desc.startswith("<html>"):
        return desc
    desc_cleaned = _replace_characters(desc)
    desc = f"<p>{desc_cleaned}</p>"
    enum_ = f"<p>{_to_html_list(enum)}</p>" if enum else ""
    node_path = f"<p><b>{node.strip()}</b></p>" if node else ""
    return "<html><body>" + desc + enum_ + node_path + "</body></html>"


def delete_device_from_node_path(path: str) -> str:
    """Delete device prefix from path.
    
    Returns:
        Path where 'DEVXXXX' prefix is subtracted.
    """
    return re.sub(r"/DEV(\d+)", "", path.upper())[0:]


def match_in_dict_keys(target: str, data: dict) -> t.Tuple[str, t.Any]:
    """Find matches for target in data keys.
    
    Returns:
        Key, value pair of the data if the target matches a key in data.
        Otherwise empty string and None
    """
    for k, v in data.items():
        if fnmatch.fnmatch(target.strip("/").lower(), f"{k.strip('/').lower()}*"):
            return k, v
    return "", None


def match_in_list(target: str, data: t.List[str]) -> str:
    """Find matches for target in given items.

    Returns:
        Item of the data where the target matches.
        Otherwise empty string.
    """
    for item in data:
        if fnmatch.fnmatch(target.strip("/").lower(), f"{item.strip('/').lower()}*"):
            return item
    return ""
