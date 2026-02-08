import os
import tempfile
from sift_search.chunker import chunk_file, chunk_directory


def test_basic_chunking():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# My Page\n\nIntro paragraph with enough text to pass the minimum length threshold.\n\n## Section One\n\nThis is the first section with real content that should become its own chunk.\n\n## Section Two\n\nThis is the second section, also with enough content to be a separate chunk.\n")
        f.flush()
        chunks = chunk_file(f.name, os.path.dirname(f.name))
    os.unlink(f.name)

    assert len(chunks) >= 2
    titles = [c["title"] for c in chunks]
    assert "Section One" in titles
    assert "Section Two" in titles


def test_title_extraction():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Getting Started\n\nThis is a guide to getting started with our product and it has enough content.\n")
        f.flush()
        chunks = chunk_file(f.name, os.path.dirname(f.name))
    os.unlink(f.name)

    assert len(chunks) >= 1
    assert chunks[0]["title"] == "Getting Started"


def test_short_sections_skipped():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Page\n\nToo short.\n\n## Real Section\n\nThis section has enough content to actually be indexed as a proper chunk.\n")
        f.flush()
        chunks = chunk_file(f.name, os.path.dirname(f.name))
    os.unlink(f.name)

    contents = [c["content"] for c in chunks]
    assert not any("Too short" in c for c in contents)


def test_url_generation():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", dir="/tmp", delete=False) as f:
        f.write("# Test\n\nEnough content here to pass the minimum length filter for chunking.\n")
        f.flush()
        chunks = chunk_file(f.name, "/tmp")
    os.unlink(f.name)

    assert len(chunks) >= 1
    assert not chunks[0]["url"].endswith(".md")


def test_chunk_directory():
    with tempfile.TemporaryDirectory() as d:
        for name in ["one.md", "two.md"]:
            with open(os.path.join(d, name), "w") as f:
                f.write(f"# {name}\n\nThis file has enough content to produce at least one chunk for testing.\n")
        chunks = chunk_directory(d)

    assert len(chunks) >= 2
