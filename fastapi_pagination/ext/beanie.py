__all__ = ["paginate"]

from typing import List, Tuple, Optional, Type, TypeVar, Union, Any

from beanie import Document
from beanie.odm.enums import SortDirection
from beanie.odm.interfaces.aggregate import DocumentProjectionType, ClientSession
from beanie.odm.queries.aggregation import AggregationQuery
from beanie.odm.queries.find import FindMany

from ..api import create_page
from ..bases import AbstractParams
from ..types import AdditionalData
from ..utils import verify_params

TDocument = TypeVar("TDocument", bound=Document)


async def paginate(
    query: Union[TDocument, FindMany[TDocument], AggregationQuery[TDocument]],
    params: Optional[AbstractParams] = None,
    *,
    additional_data: AdditionalData = None,
    projection_model: Optional[Type[DocumentProjectionType]] = None,
    sort: Union[None, str, List[Tuple[str, SortDirection]]] = None,
    session: Optional[ClientSession] = None,
    ignore_cache: bool = False,
    fetch_links: bool = False,
    lazy_parse: bool = False,
    **pymongo_kwargs: Any,
) -> Any:
    params, raw_params = verify_params(params, "limit-offset")

    if isinstance(query, AggregationQuery):
        aggregation_query = query.clone()  # type: ignore
        paginate_data = []
        if raw_params.limit is not None:
            paginate_data.append({"$limit": raw_params.limit + (raw_params.offset or 0)})
        if raw_params.offset is not None:
            paginate_data.append({"$skip": raw_params.offset})

        aggregation_query.aggregation_pipeline.extend(
            [
                {"$facet": {"metadata": [{"$count": "total"}], "data": paginate_data}},
            ]
        )
        data = (await aggregation_query.to_list())[0]
        items = data["data"]
        try:
            total = data["metadata"][0]["total"]
        except IndexError:
            total = 0
    else:
        items = await query.find_many(
            limit=raw_params.limit,
            skip=raw_params.offset,
            projection_model=projection_model,
            sort=sort,
            session=session,
            ignore_cache=ignore_cache,
            fetch_links=fetch_links,
            lazy_parse=lazy_parse,
            **pymongo_kwargs,
        ).to_list()
        total = await query.find(
            {}, session=session, ignore_cache=ignore_cache, fetch_links=False, **pymongo_kwargs
        ).count()

    return create_page(items, total, params, **(additional_data or {}))
