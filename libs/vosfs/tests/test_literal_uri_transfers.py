"""Literal filenames must identify the same node in metadata and transfers."""

from xml.etree import ElementTree as ET

import httpx
import pytest
import respx
from conftest import AUTHORITY, SYNC_URL, make_sim_fs
from vospace_sim import VOSpaceSim


@pytest.mark.parametrize("redirect", [False, True])
@pytest.mark.parametrize("path", ["/100%41", "/part?x#y", "/a b", "/café"])
async def test_async_transfers_preserve_literal_names(router: respx.Router, path: str, redirect: bool) -> None:
    sim = VOSpaceSim().add_file(path, b"original").add_file("/100A", b"neighbour")
    fs = make_sim_fs(router, sim)

    def negotiate(request: httpx.Request) -> httpx.Response:
        if not redirect and request.url.params.get("REQUEST") == "redirect":
            return httpx.Response(400)
        return sim._negotiate(request)

    router.post(SYNC_URL).mock(side_effect=negotiate)
    try:
        assert await fs._cat_file(path) == b"original"
        await fs._pipe_file(path, b"replacement")
        assert await fs._cat_file(path) == b"replacement"
        assert await fs._cat_file("/100A") == b"neighbour"
    finally:
        await fs.aclose()


def test_sync_transfers_keep_literal_percent_distinct_from_its_decoded_name(router: respx.Router) -> None:
    sim = VOSpaceSim().add_file("/100%41", b"original").add_file("/100A", b"neighbour")
    fs = make_sim_fs(router, sim, asynchronous=False)
    try:
        assert fs.cat_file("/100%41") == b"original"
        fs.pipe_file("/100%41", b"replacement")
        assert fs.cat_file("/100%41") == b"replacement"
        assert fs.cat_file("/100A") == b"neighbour"
    finally:
        fs.close()


@pytest.mark.parametrize(
    ("path", "wire_path"),
    [("/100%41", "/100%2541"), ("/part?x#y", "/part%3Fx%23y"), ("/a b", "/a%20b")],
)
async def test_container_uri_matches_its_encoded_request_path(router: respx.Router, path: str, wire_path: str) -> None:
    sim = VOSpaceSim()
    fs = make_sim_fs(router, sim)
    try:
        await fs._mkdir(path, create_parents=False)
        request = next(call.request for call in router.calls if call.request.method == "PUT")
        document = ET.fromstring(request.content)  # noqa: S314 - locally generated request XML
        assert document.get("uri") == f"vos://{AUTHORITY}{wire_path}"
        assert request.url.raw_path.decode().endswith(wire_path)
        assert await fs._isdir(path)
    finally:
        await fs.aclose()
