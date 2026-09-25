"""Acesso somente-leitura a um pacote MUGEN (pasta ou .zip), com resolucao de caminho case-insensitive."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path, PurePosixPath


class Source:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._zip = zipfile.ZipFile(self.path) if self.path.suffix.lower() == ".zip" else None
        if self._zip:
            names = [n for n in self._zip.namelist() if not n.endswith("/")]
        else:
            names = [p.relative_to(self.path).as_posix() for p in sorted(self.path.rglob("*")) if p.is_file()]
        self._names = {n.lower(): n for n in names}
        self.files = sorted(names)

    def sha256(self) -> str:
        h = hashlib.sha256()
        if self._zip:
            h.update(self.path.read_bytes())
        else:
            for n in self.files:
                h.update(n.encode())
                h.update(self.read(n))
        return h.hexdigest()

    def find(self, rel: str, base: str = "") -> str | None:
        """Resolve 'rel' relativo a 'base' (pasta do .def), ignorando caixa e barras invertidas."""
        rel = rel.strip().strip('"').replace("\\", "/")
        cands = [str(PurePosixPath(base) / rel) if base else rel, rel]
        for c in cands:
            n = self._names.get(str(PurePosixPath(c)).lower())
            if n:
                return n
        # MUGEN tambem procura pelo nome do arquivo em qualquer pasta do pacote
        leaf = PurePosixPath(rel).name.lower()
        hits = [v for k, v in self._names.items() if PurePosixPath(k).name == leaf]
        return hits[0] if len(hits) == 1 else None

    def read(self, name: str) -> bytes:
        if self._zip:
            return self._zip.read(name)
        return (self.path / name).read_bytes()

    def defs(self) -> list[str]:
        return [n for n in self.files if n.lower().endswith(".def")]
