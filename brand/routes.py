from fastapi import APIRouter

from brand.views import onboard_brand

router = APIRouter(prefix="/collection_dna", tags=["collection-dna"])

router.add_api_route(
    path="/brand/onboard",
    endpoint=onboard_brand,
    methods=["POST"],
    summary="Onboard a new brand",
    description="Start brand onboarding workflow. Extracts brand DNA and classification.",
)



# router_v2 = APIRouter(prefix="/brand-identity")
# router_v2.add_api_route(
#     path="",
#     endpoint=trigger_identification_workflow_v2,
#     methods=["POST"],
#     description="Triggers brand identification workflow"
# )
#
# router_v2.add_api_route(
#     path="",
#     endpoint=get_brands,
#     methods=["GET"],
#     description="Get brands with optional filters for brand_type and status"
# )
#
# router_v2.add_api_route(
#     path="/sota/distinct",
#     endpoint=get_distinct_sota_brands,
#     methods=["GET"],
#     description="Get all distinct SOTA brands by brand_name with latest created_at"
# )
