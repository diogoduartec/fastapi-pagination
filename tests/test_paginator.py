from typing import Generic, TypeVar

from fastapi import FastAPI
from pytest import fixture, mark

from fastapi_pagination import (
    LimitOffsetPage,
    Page,
    Params,
    add_pagination,
    paginate,
    set_page,
)
from fastapi_pagination.default import OptionalParams
from fastapi_pagination.limit_offset import OptionalLimitOffsetParams

from .base import BasePaginationTestCase
from .utils import OptionalPage, OptionalLimitOffsetPage


class TestPaginationParams(BasePaginationTestCase):
    @fixture(scope="session")
    def app(self, model_cls, entities):
        app = FastAPI()

        @app.get("/default", response_model=Page[model_cls])
        @app.get("/limit-offset", response_model=LimitOffsetPage[model_cls])
        @app.get("/optional/default", response_model=OptionalPage[model_cls])
        @app.get("/optional/limit-offset", response_model=OptionalLimitOffsetPage[model_cls])
        async def route():
            return paginate(entities)

        return add_pagination(app)

    @mark.parametrize(
        "path,cls_name,params",
        [
            ("/optional/default", "optional_page", OptionalParams()),
            ("/optional/limit-offset", "optional_limit_offset_page", OptionalLimitOffsetParams()),
        ],
        ids=[
            "default",
            "limit-offset",
        ],
    )
    async def test_optional_params(
        self,
        client,
        params,
        entities,
        cls_name,
        additional_params,
        result_model_cls,
        path,
    ):
        await self.run_pagination_test(
            client,
            path,
            params,
            entities,
            cls_name,
            additional_params,
            result_model_cls,
        )


T = TypeVar("T")


class CustomPage(Page[T], Generic[T]):
    new_field: int


def test_paginator_additional_data():
    with set_page(CustomPage):
        page = paginate([], Params(), additional_data={"new_field": 10})

    assert page == CustomPage(items=[], total=0, page=1, pages=0, size=50, new_field=10)
