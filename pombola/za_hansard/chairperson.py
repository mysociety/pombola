import bleach
import re

from bs4 import NavigableString

# For checking regressions, just a note that the following committee
# meeting IDs are known to work:
#   8655
#   8567
#   8593
#   6040
#   6256
#   5593
#   8564
#   8220
#   10052
#   9956
#   7941
#   7612
#   8208

def strip_tags_from_html(html):
    allowed_tags = bleach.ALLOWED_TAGS + [
        'br', 'p', 'div', 'h1', 'h2', 'h3', 'h4'
    ]
    return bleach.clean(
        html,
        tags=allowed_tags,
        strip=True
    )

def get_from_text_version(soup):
    """e.g. for meeting with ID: 6040, 8564"""

    text = soup.get_text('_')
    m = re.search(
        r'_\s*(?:Acting\s*)?Chair(?:person)?\s*:?[\s_]*([^_]*)_[\s_]*Documents?\s+handed\s+out',
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    # Another thing to check is that sometimes we just get a mention
    # of the chairperson in the body of the text, like:
    # 'The Chairperson, Mr Holomisa, informed the committee' (from 6256)
    # (You need to allow '.' in the name because the title 'Adv.' is sometimes
    # used.)
    m = re.search(
        r'The\s+[Cc]hairperson\s*,\s*([a-zA-Z \.-]+)\s*,',
        text,
    )
    if m:
        return m.group(1).strip()
    # Another possibility is that the chairperson is introduced with:
    # "The meeting was Chaired by ..." (e.g. 5593)
    m = re.search(
        r'_\s*The meeting was [cC]haired by ([^_]*)_',
        text
    )
    if m:
        return m.group(1).strip()
