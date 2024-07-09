from fastapi.responses import JSONResponse, PlainTextResponse


class APIResponse:
    @staticmethod
    def as_json(code: int, status: str, data=None, detail: str = None) -> JSONResponse:
        content = {
            "code": code,
            "status": status,
        }
        if data:
            content.update({"data": data})
        if detail:
            content.update({"detail": detail})
        return JSONResponse(status_code=code, content=content)

    @staticmethod
    def as_text(code: int, message: str) -> PlainTextResponse:
        return PlainTextResponse(status_code=code, content=message)
