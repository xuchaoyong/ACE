#!/usr/bin/env python3
"""
Extract structured CLI knowledge from Huawei HEDEx command manuals.

The script follows the "network assimilation" idea used by NAssim: convert
vendor-specific, human-oriented CLI documents into a normalized command model
that can be consumed by configuration generation, recall, and repair systems.

Example:
  python3 bin/nassim_cli_manual_extractor.py \
    --url 'https://support.huawei.com/hedex/hdx.do?docid=EDOC1100218869&tocURL=resources/hedex-homepage.html' \
    --command 8021p-inbound \
    --output 8021p-inbound.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_URL = (
    "https://support.huawei.com/hedex/hdx.do?"
    "docid=EDOC1100218869&tocURL=resources/hedex-homepage.html"
)

BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "caption",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


def normalize_inline(text: str) -> str:
    """Collapse whitespace inside one logical line."""

    return re.sub(r"\s+", " ", text).strip()


def normalize_block(text: str) -> str:
    """Normalize human-readable block text while preserving paragraph breaks."""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_nonempty_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


@dataclass
class Node:
    tag: str
    attrs: Dict[str, str] = field(default_factory=dict)
    children: List[object] = field(default_factory=list)
    parent: Optional["Node"] = None

    def append(self, child: object) -> None:
        self.children.append(child)
        if isinstance(child, Node):
            child.parent = self

    def attr(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)

    def has_class(self, class_name: str) -> bool:
        return class_name in self.attr("class").split()

    def find_all(
        self,
        tag: Optional[str] = None,
        class_name: Optional[str] = None,
    ) -> List["Node"]:
        found: List[Node] = []
        for child in self.children:
            if not isinstance(child, Node):
                continue
            tag_ok = tag is None or child.tag == tag
            class_ok = class_name is None or child.has_class(class_name)
            if tag_ok and class_ok:
                found.append(child)
            found.extend(child.find_all(tag=tag, class_name=class_name))
        return found

    def first(
        self,
        tag: Optional[str] = None,
        class_name: Optional[str] = None,
    ) -> Optional["Node"]:
        matches = self.find_all(tag=tag, class_name=class_name)
        return matches[0] if matches else None

    def text(self, block: bool = True, var_brackets: bool = False) -> str:
        pieces = list(_node_text(self, block=block, var_brackets=var_brackets))
        text = "".join(pieces)
        return normalize_block(text) if block else normalize_inline(text)


class SimpleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: Sequence[Tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        attr_dict = {name.lower(): value or "" for name, value in attrs}
        node = Node(tag=tag, attrs=attr_dict)
        self.stack[-1].append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return

        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data:
            self.stack[-1].append(data)


def _node_text(node: Node, block: bool, var_brackets: bool) -> Iterator[str]:
    if node.tag == "br":
        yield "\n"
        return

    wraps_var = var_brackets and (
        node.has_class("varname") or node.tag == "varname"
    )
    if wraps_var:
        inner_parts: List[str] = []
        for child in node.children:
            if isinstance(child, Node):
                inner_parts.extend(_node_text(child, block=False, var_brackets=False))
            else:
                inner_parts.append(str(child))
        inner = normalize_inline("".join(inner_parts))
        if inner:
            yield f"<{inner}>"
        return

    if block and node.tag in BLOCK_TAGS and node.tag not in {"document"}:
        yield "\n"

    for child in node.children:
        if isinstance(child, Node):
            yield from _node_text(child, block=block, var_brackets=var_brackets)
        else:
            yield str(child)

    if block and node.tag in BLOCK_TAGS and node.tag not in {"document", "br"}:
        yield "\n"


def parse_html(html: str) -> Node:
    parser = SimpleHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.root


def meta_content(root: Node, name: str) -> str:
    for meta in root.find_all("meta"):
        if meta.attr("name").lower() == name.lower():
            return meta.attr("content")
    return ""


def section_map(root: Node) -> Dict[str, Node]:
    """Return H2 section title -> containing section div."""

    sections: Dict[str, Node] = {}
    for h2 in root.find_all("h2", class_name="sectiontitle"):
        title = h2.text(block=False)
        if title and h2.parent:
            sections[title] = h2.parent
    return sections


def body_children_after_heading(section: Node) -> List[Node]:
    children: List[Node] = []
    seen_heading = False
    for child in section.children:
        if not isinstance(child, Node):
            continue
        if child.tag == "h2" and child.has_class("sectiontitle"):
            seen_heading = True
            continue
        if seen_heading:
            children.append(child)
    return children


def section_text(section: Optional[Node]) -> str:
    if not section:
        return ""
    wrapper = Node("section")
    for child in body_children_after_heading(section):
        wrapper.append(child)
    return wrapper.text(block=True)


def paragraph_lines(section: Optional[Node], var_brackets: bool = False) -> List[str]:
    if not section:
        return []
    lines: List[str] = []
    for child in body_children_after_heading(section):
        for para in child.find_all("p"):
            text = para.text(block=False, var_brackets=var_brackets)
            if text:
                lines.append(text)
    if lines:
        return lines
    return split_nonempty_lines(section_text(section))


def table_rows(table: Node) -> List[List[Node]]:
    rows: List[List[Node]] = []
    for tr in table.find_all("tr"):
        cells = [cell for cell in tr.children if isinstance(cell, Node) and cell.tag in {"td", "th"}]
        if cells:
            rows.append(cells)
    return rows


def extract_parameters(section: Optional[Node]) -> List[Dict[str, str]]:
    if not section:
        return []

    tables: List[Node] = []
    for child in body_children_after_heading(section):
        tables.extend(child.find_all("table"))
        if child.tag == "table":
            tables.append(child)

    if not tables:
        return []

    params: List[Dict[str, str]] = []
    for row in table_rows(tables[0]):
        if not row or row[0].tag == "th":
            continue
        if len(row) < 2:
            continue
        parameter = row[0].text(block=False)
        info_parts = [cell.text(block=True) for cell in row[1:] if cell.text(block=True)]
        info = normalize_block("\n".join(info_parts))
        if parameter:
            params.append({"Parameters": parameter, "Info": info})
    return params


def extract_examples(section: Optional[Node]) -> List[List[str]]:
    if not section:
        return []
    examples: List[List[str]] = []
    for child in body_children_after_heading(section):
        pre_nodes = child.find_all("pre")
        if child.tag == "pre":
            pre_nodes.insert(0, child)
        for pre in pre_nodes:
            lines = split_nonempty_lines(pre.text(block=True))
            if lines:
                examples.append(lines)
    return examples


def extract_manual(html: str) -> Dict[str, object]:
    root = parse_html(html)
    sections = section_map(root)

    title_node = root.first("h1", class_name="topicTitle-h1") or root.first("title")
    title = title_node.text(block=False) if title_node else ""
    if not title:
        title = meta_content(root, "DC.Title")

    function_text = section_text(sections.get("Function"))
    cli_lines = paragraph_lines(sections.get("Format"), var_brackets=True)
    views = paragraph_lines(sections.get("Views"))
    parameters = extract_parameters(sections.get("Parameters"))
    examples = extract_examples(sections.get("Example"))

    # CLI references keep scenario, impact, and precautions under this section.
    extra_info = section_text(sections.get("Usage Guidelines"))

    return {
        "PageTitle": title,
        "FuncDef": function_text,
        "CLIs": cli_lines,
        "ParentView": views,
        "ParaDef": parameters,
        "Examples": examples,
        "ExtraInfo": extra_info,
    }


class HedexClient:
    def __init__(
        self,
        entry_url: str,
        sleep_seconds: float = 0.0,
        timeout: int = 30,
        retries: int = 2,
    ) -> None:
        parsed = urlparse(entry_url)
        self.entry_url = entry_url
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.docid = parse_qs(parsed.query).get("docid", [""])[0]
        if not self.docid:
            raise ValueError("The HEDEx URL must include docid=...")
        self.sleep_seconds = sleep_seconds
        self.timeout = timeout
        self.retries = retries
        self._topic_info: Optional[Dict[str, object]] = None
        self._subnode_cache: Dict[str, List[Dict[str, object]]] = {}

    def _request(self, path: str, params: Optional[Dict[str, str]] = None) -> bytes:
        if params:
            path = f"{path}?{urlencode(params)}"
        url = urljoin(self.origin, path)
        headers = {
            "Accept": "application/json, text/html, text/plain, */*",
            "Referer": self.entry_url,
            "User-Agent": "Mozilla/5.0 (compatible; nassim-cli-manual-extractor/1.0)",
        }
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            if self.sleep_seconds:
                time.sleep(self.sleep_seconds)
            try:
                with urlopen(Request(url, headers=headers), timeout=self.timeout) as response:
                    return response.read()
            except (HTTPError, URLError, TimeoutError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(2**attempt)
        assert last_error is not None
        raise last_error

    def json_get(self, path: str, params: Optional[Dict[str, str]] = None) -> object:
        data = self._request(path, params=params)
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, dict) and payload.get("status") != 200:
            raise RuntimeError(f"HEDEx API error: {payload}")
        return payload.get("data") if isinstance(payload, dict) else payload

    def topic_info(self) -> Dict[str, object]:
        if self._topic_info is None:
            data = self.json_get(f"/hedex/api/navi/{self.docid}/topic")
            if not isinstance(data, dict):
                raise RuntimeError("Unexpected topic API response")
            self._topic_info = data
        return self._topic_info

    def base_topic(self) -> Dict[str, str]:
        info = self.topic_info()
        topic = info.get("topicInfo") or {}
        if not isinstance(topic, dict):
            raise RuntimeError("Missing topicInfo in HEDEx response")
        return {
            "topicLibId": str(topic.get("topicLibId") or ""),
            "topicLibVer": str(topic.get("topicLibVer") or ""),
        }

    def first_level_tree(self) -> List[Dict[str, object]]:
        data = self.json_get(f"/hedex/api/navi/{self.docid}/first-level-tree")
        if not isinstance(data, list):
            raise RuntimeError("Unexpected first-level tree response")
        return data

    def sub_nodes(self, position: str) -> List[Dict[str, object]]:
        if position in self._subnode_cache:
            return self._subnode_cache[position]
        data = self.json_get(f"/hedex/api/navi/{self.docid}/position/{quote(position, safe='.')}/sub-nodes")
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected sub-node response for {position}")
        self._subnode_cache[position] = data
        return data

    def walk(self, roots: Iterable[Dict[str, object]]) -> Iterator[Dict[str, object]]:
        stack = list(reversed(list(roots)))
        while stack:
            node = stack.pop()
            yield node
            if node.get("isParent"):
                position = str(node.get("position") or "")
                if not position:
                    continue
                children = self.sub_nodes(position)
                stack.extend(reversed(children))

    def find_command_node(
        self,
        command: str,
        root_position: Optional[str] = None,
        max_nodes: Optional[int] = None,
    ) -> Dict[str, object]:
        roots = self.sub_nodes(root_position) if root_position else self.first_level_tree()
        command_key = command.casefold()
        fallback: Optional[Dict[str, object]] = None

        for index, node in enumerate(self.walk(roots), start=1):
            if max_nodes and index > max_nodes:
                break
            title = str(node.get("topicTitle") or "")
            title_key = title.casefold()
            if title_key == command_key:
                return node
            if fallback is None and command_key in title_key:
                fallback = node

        if fallback:
            return fallback
        raise LookupError(f"Command not found in HEDEx navigation: {command}")

    def command_leaves(
        self,
        root_position: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterator[Dict[str, object]]:
        roots = self.sub_nodes(root_position) if root_position else self.first_level_tree()
        count = 0
        for node in self.walk(roots):
            if not node.get("isParent"):
                topic_url = str(node.get("topicUrl") or "")
                if "/command/" not in topic_url:
                    continue
                yield node
                count += 1
                if limit and count >= limit:
                    return

    def fetch_page(self, node_or_topic_url: object) -> str:
        if isinstance(node_or_topic_url, dict):
            topic_url = str(node_or_topic_url.get("topicUrl") or "")
            topic_lib_id = str(node_or_topic_url.get("topicLibId") or "")
            topic_lib_ver = str(node_or_topic_url.get("topicLibVer") or "")
        else:
            topic_url = str(node_or_topic_url)
            base = self.base_topic()
            topic_lib_id = base["topicLibId"]
            topic_lib_ver = base["topicLibVer"]

        if not topic_url:
            raise ValueError("Missing topicUrl for page fetch")
        if not topic_lib_id or not topic_lib_ver:
            raise ValueError("Missing topicLibId/topicLibVer for page fetch")

        safe_topic = quote(topic_url, safe="/._-()")
        path = f"/hedex/api/pages/{self.docid}/{topic_lib_id}/{topic_lib_ver}/{safe_topic}"
        return self._request(path).decode("utf-8", errors="replace")


def add_source_metadata(record: Dict[str, object], node: Optional[Dict[str, object]], client: HedexClient) -> Dict[str, object]:
    if not node:
        return record
    topic_url = str(node.get("topicUrl") or "")
    if topic_url:
        record["_Source"] = {
            "docid": client.docid,
            "topicId": node.get("topicId"),
            "topicUrl": topic_url,
            "position": node.get("position"),
            "pageNum": node.get("pageNum"),
            "url": f"{client.origin}/hedex/hdx.do?docid={client.docid}&tocURL={topic_url}",
        }
    return record


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crawl Huawei HEDEx command manuals and emit NAssim-style structured CLI JSON.",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="HEDEx entry URL that contains docid=...")
    parser.add_argument("--command", help="Command title to locate in the HEDEx navigation tree, for example: 8021p-inbound")
    parser.add_argument("--topic-url", help="Direct HEDEx topic URL, for example: resources/command/8090/8021P-INBOUND.html")
    parser.add_argument("--all", action="store_true", help="Extract all command leaf pages below the selected root")
    parser.add_argument("--root-position", help="Navigation position to start from, for example: 8.1.6.14.3")
    parser.add_argument("--limit", type=int, help="Maximum number of command pages to extract with --all")
    parser.add_argument("--max-search-nodes", type=int, help="Maximum navigation nodes to inspect when resolving --command")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay between HTTP requests, in seconds")
    parser.add_argument("--output", "-o", help="Write JSON to this file instead of stdout")
    parser.add_argument("--no-source", action="store_true", help="Do not include _Source metadata in the output")
    parser.add_argument("--compact", action="store_true", help="Emit compact JSON")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if sum(bool(x) for x in [args.command, args.topic_url, args.all]) != 1:
        print("Specify exactly one of --command, --topic-url, or --all.", file=sys.stderr)
        return 2

    client = HedexClient(args.url, sleep_seconds=args.sleep)

    try:
        if args.command:
            node = client.find_command_node(
                args.command,
                root_position=args.root_position,
                max_nodes=args.max_search_nodes,
            )
            record = extract_manual(client.fetch_page(node))
            result: object = record if args.no_source else add_source_metadata(record, node, client)
        elif args.topic_url:
            record = extract_manual(client.fetch_page(args.topic_url))
            result = record
        else:
            records: List[Dict[str, object]] = []
            for node in client.command_leaves(root_position=args.root_position, limit=args.limit):
                record = extract_manual(client.fetch_page(node))
                if not args.no_source:
                    add_source_metadata(record, node, client)
                records.append(record)
            result = records
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    indent = None if args.compact else 2
    payload = json.dumps(result, ensure_ascii=False, indent=indent)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fp:
            fp.write(payload)
            fp.write("\n")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
