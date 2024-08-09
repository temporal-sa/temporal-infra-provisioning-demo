from typing import Iterable, List

import cramjam
from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec


class CompressionCodec(PayloadCodec):
    async def encode(self, payloads: Iterable[Payload]) -> List[Payload]:
        return [
            Payload(
                metadata={
                    "encoding": b"binary/snappy",
                },
                data=(bytes(cramjam.snappy.compress(p.SerializeToString()))),
            )
            for p in payloads
        ]

    async def decode(self, payloads: Iterable[Payload]) -> List[Payload]:
        ret: List[Payload] = []
        for p in payloads:
            if p.metadata.get("encoding", b"").decode() != "binary/snappy":
                ret.append(p)
                continue
            ret.append(Payload.FromString(bytes(cramjam.snappy.decompress(p.data))))
        return ret
