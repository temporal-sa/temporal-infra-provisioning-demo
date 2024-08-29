"""Temporal Python Codec Server

Usage:
  codec_server.py
  codec_server.py --web <url>

Options:
  --web    Temporal Web UI URL to enable CORS for

"""
from docopt import docopt

from functools import partial
from typing import Awaitable, Callable, Iterable, List

from aiohttp import hdrs, web
from google.protobuf import json_format
from temporalio.api.common.v1 import Payload, Payloads

from codec import CompressionCodec, EncryptionCodec

def build_codec_server(arguments) -> web.Application:
	async def header_options(req: web.Request) -> web.Response:
		resp = web.Response()
		if arguments["--web"]==True:
			if req.headers.get(hdrs.ORIGIN) == arguments["<url>"]:
				resp.headers[hdrs.ACCESS_CONTROL_ALLOW_ORIGIN] = arguments["<url>"]
				resp.headers[hdrs.ACCESS_CONTROL_ALLOW_METHODS] = "POST"
				resp.headers[hdrs.ACCESS_CONTROL_ALLOW_HEADERS] = "content-type,x-namespace"
		return resp

	# General purpose payloads-to-payloads
	async def apply(
		fn: Callable[[Iterable[Payload]], Awaitable[List[Payload]]], req: web.Request
	) -> web.Response:
		# Read payloads as JSON
		assert req.content_type == "application/json"
		payloads = json_format.Parse(await req.read(), Payloads())

		# Apply
		payloads = Payloads(payloads=await fn(payloads.payloads))

		# Apply headers and return JSON
		resp = await header_options(req)
		resp.content_type = "application/json"
		resp.text = json_format.MessageToJson(payloads)
		return resp

	async def root_handler(req: web.Request) -> web.Response:
		# TODO: get the port instead of hardcoding, make it more clear that we are accepting CORS
		# requests from a specific URL that is passed in through --web.
		return web.Response(text="Codec Server running on port 8081")

	# Build app per-Namespace
	app = web.Application()
	codecs = {
		"encryption_codec": EncryptionCodec(),
		"compression_codec": CompressionCodec(),
	}
	for route,codec in codecs.items():
		app.add_routes(
			[
				web.post(("/" + route + "/encode"), partial(apply, codec.encode)),
				web.post(("/" + route + "/decode"), partial(apply, codec.decode)),
				web.options(("/" + route + "/decode"), header_options),
			]
		)
		app.router.add_get("/", root_handler)

	return app

if __name__ == "__main__":
	arguments = docopt(__doc__)
	web.run_app(build_codec_server(arguments), host="127.0.0.1", port=8081)
