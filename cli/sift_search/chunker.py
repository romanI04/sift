"""Split markdown files into searchable chunks."""

import os
import re


def chunk_file(filepath, base_dir):
    """Read a markdown file and split into chunks.

    Returns list of dicts: {url, title, content}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    rel_path = os.path.relpath(filepath, base_dir)
    # Convert file path to URL-like path (strip .md extension)
    url = rel_path.replace(os.sep, "/")
    if url.endswith(".md"):
        url = url[:-3]

    # Extract document title from first H1, or use filename
    doc_title = os.path.splitext(os.path.basename(filepath))[0]
    h1_match = re.match(r"^#\s+(.+)$", text, re.MULTILINE)
    if h1_match:
        doc_title = h1_match.group(1).strip()

    # Split by H2/H3 headers
    sections = re.split(r"(?=^#{2,3}\s+)", text, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract section header if present
        header_match = re.match(r"^(#{2,3})\s+(.+)$", section, re.MULTILINE)
        if header_match:
            title = header_match.group(2).strip()
            body = section[header_match.end() :].strip()
        else:
            title = doc_title
            body = section

        # Strip the H1 line from body if it's the first section
        body = re.sub(r"^#\s+.+\n*", "", body).strip()

        if not body or len(body) < 30:
            continue

        # If section is too long, split on paragraphs
        if len(body) > 1000:
            paragraphs = re.split(r"\n\n+", body)
            buf = ""
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                if buf and len(buf) + len(para) > 800:
                    if len(buf) >= 30:
                        chunks.append({"url": url, "title": title, "content": buf})
                    buf = para
                else:
                    buf = f"{buf}\n\n{para}" if buf else para
            if buf and len(buf) >= 30:
                chunks.append({"url": url, "title": title, "content": buf})
        else:
            chunks.append({"url": url, "title": title, "content": body})

    return chunks


def chunk_directory(directory):
    """Walk a directory and chunk all markdown files.

    Returns list of chunk dicts.
    """
    all_chunks = []
    for root, _dirs, files in os.walk(directory):
        for fname in sorted(files):
            if fname.endswith(".md"):
                fpath = os.path.join(root, fname)
                all_chunks.extend(chunk_file(fpath, directory))
    return all_chunks
