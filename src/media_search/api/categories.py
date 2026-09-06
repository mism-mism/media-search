from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from media_search.adapters.gemini_categories import normalize_reference
from media_search.application.categories import CategoryService
from media_search.ports.import_lock import ImportLockBusy

MAX_UPLOAD_BYTES = 30 * 1024 * 1024


def _output(category):
    return {'category_id': category.category_id, 'name': category.name, 'criteria': category.criteria,
            'reference_urls': [f'/api/library/categories/{category.category_id}/references/{i}'
                               for i in range(len(category.references))]}


def category_router(service: CategoryService) -> APIRouter:
    router = APIRouter(prefix='/api/library/categories')

    @router.get('')
    def list_categories():
        return {'categories': [_output(c) for c in service.list_all()],
                'enabled': service.enabled, 'max_per_import': service.max_per_import}

    @router.post('', status_code=201)
    async def create_category(name: str = Form(), criteria: str = Form(), references: list[UploadFile] = File()):
        if not 1 <= len(references) <= 3:
            raise HTTPException(400, '見本画像は1〜3枚を選択してください')
        try:
            normalized = []
            for file in references:
                raw = await file.read(MAX_UPLOAD_BYTES + 1)
                if len(raw) > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, '見本画像は1枚30MBまでです')
                normalized.append(normalize_reference(raw))
            return _output(service.create(name=name, criteria=criteria, references=tuple(normalized)))
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None
        except ImportLockBusy:
            raise HTTPException(409, {'error': 'import_busy'}) from None

    @router.get('/{category_id}/references/{index}')
    def reference(category_id: str, index: int):
        try:
            return Response(service.reference(category_id, index), media_type='image/jpeg',
                            headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})
        except FileNotFoundError:
            raise HTTPException(404, '見本画像が見つかりません') from None

    @router.delete('/{category_id}')
    def delete_category(category_id: str):
        try:
            service.delete(category_id)
            return {'status': 'deleted'}
        except FileNotFoundError:
            raise HTTPException(404, 'カテゴリが見つかりません') from None
        except ImportLockBusy:
            raise HTTPException(409, {'error': 'import_busy'}) from None

    return router
