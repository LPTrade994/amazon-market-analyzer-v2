from __future__ import annotations

WEIGHTS = {
    "margin": 0.35,
    "demand": 0.20,
    "competition": 0.12,
    "availability": 0.10,
    "priceedge": 0.10,
    "logistics": 0.06,
    "risk": 0.04,
    "stability": 0.03,
}

ALIAS_MAP = {
    "locale": "locale",
    "title": "title",
    "asin": "asin",
    "parent asin": "parent_asin",
    "brand": "brand",
    "brand store url": "brand_store_url",
    "variation count": "variation_count",
    "categories: root": "category_root",
    "categories: sub": "category_sub",
    "url: amazon": "url_amazon",
    "url: keepa": "url_keepa",

    "sales rank: current": "sales_rank_current",
    "sales rank: 30 days avg.": "sales_rank_30d_avg",
    "sales rank: 90 days avg.": "sales_rank_90d_avg",
    "sales rank: 180 days avg.": "sales_rank_180d_avg",
    "sales rank: 365 days avg.": "sales_rank_365d_avg",
    "sales rank: 30 days drop %": "sales_rank_30d_drop_pct",
    "sales rank: 90 days drop %": "sales_rank_90d_drop_pct",
    "sales rank: drops last 30 days": "sales_rank_drops_30d",
    "sales rank: drops last 90 days": "sales_rank_drops_90d",
    "bought in past month": "bought_past_month",
    "90 days change % monthly sold": "chg_90d_monthly_sold",

    "reviews: rating": "reviews_rating",
    "reviews: rating count": "reviews_count",
    "reviews: rating count - 30 days avg.": "reviews_30d_avg",
    "reviews: rating count - 90 days avg.": "reviews_90d_avg",

    "buy box 🚚: current": "buybox_current",
    "buy box 🚚: 30 days avg.": "buybox_30d_avg",
    "buy box 🚚: 90 days avg.": "buybox_90d_avg",
    "buy box 🚚: 180 days avg.": "buybox_180d_avg",
    "buy box 🚚: 365 days avg.": "buybox_365d_avg",
    "buy box 🚚: 30 days drop %": "buybox_30d_drop_pct",
    "buy box 🚚: is lowest": "buybox_is_lowest",
    "buy box 🚚: lowest": "buybox_lowest",
    "buy box 🚚: highest": "buybox_highest",
    "buy box 🚚: 90 days oos": "buybox_90d_oos",
    "buy box: % amazon 30 days": "buybox_pct_amz_30d",
    "buy box: % amazon 90 days": "buybox_pct_amz_90d",
    "buy box: % amazon 180 days": "buybox_pct_amz_180d",
    "buy box: % amazon 365 days": "buybox_pct_amz_365d",
    "buy box: winner count 30 days": "buybox_winner_cnt_30d",
    "buy box: winner count 90 days": "buybox_winner_cnt_90d",
    "buy box: standard deviation 30 days": "buybox_std_30d",
    "buy box: standard deviation 90 days": "buybox_std_90d",
    "buy box: standard deviation 365 days": "buybox_std_365d",
    "buy box: flipability 30 days": "flipability_30d",
    "buy box: flipability 90 days": "flipability_90d",
    "buy box: flipability 365 days": "flipability_365d",
    "buy box: unqualified": "buybox_unqualified",

    "competitive price threshold": "competitive_price_threshold",
    "suggested lower price": "suggested_lower_price",

    "amazon: current": "amazon_current",
    "amazon: 30 days avg.": "amazon_30d_avg",
    "amazon: 90 days avg.": "amazon_90d_avg",
    "amazon: 180 days avg.": "amazon_180d_avg",
    "amazon: 365 days avg.": "amazon_365d_avg",
    "amazon: is lowest": "amazon_is_lowest",
    "amazon: lowest": "amazon_lowest",
    "amazon: highest": "amazon_highest",
    "amazon: 90 days oos": "amazon_90d_oos",
    "amazon: oos count 30 days": "amazon_oos_cnt_30d",
    "amazon: oos count 90 days": "amazon_oos_cnt_90d",
    "amazon: availability of the amazon offer": "amazon_offer_availability",
    "amazon: amazon offer shipping delay": "amazon_offer_shipping_delay",

    "new: current": "new_current",
    "new: 30 days avg.": "new_30d_avg",
    "new: 90 days avg.": "new_90d_avg",
    "new: 180 days avg.": "new_180d_avg",
    "new: 365 days avg.": "new_365d_avg",
    "new: is lowest": "new_is_lowest",
    "new: lowest": "new_lowest",
    "new: highest": "new_highest",

    "new, 3rd party fba: current": "new_3p_fba_current",
    "new, 3rd party fbm 🚚: current": "new_3p_fbm_current",

    "fba pick&pack fee": "fba_pickpack_fee",
    "referral fee %": "referral_fee_pct",
    "referral fee based on current buy box price": "referral_fee_on_bb",
    "prime eligible (buy box)": "prime_eligible",
    "map restriction": "map_restriction",

    "total offer count": "total_offer_count",
    "new offer count: current": "new_offer_count_current",
    "new offer count: 30 days avg.": "new_offer_count_30d_avg",
    "used offer count: current": "used_offer_count_current",

    "list price: current": "list_price_current",
    "lightning deals: current": "lightning_deals_current",
    "lightning deals: is lowest": "lightning_deals_is_lowest",

    "last price change": "last_price_change",
    "last update": "last_update",

    "package: dimension (cm³)": "package_volume_cm3",
    "package: length (cm)": "package_length_cm",
    "package: width (cm)": "package_width_cm",
    "package: height (cm)": "package_height_cm",
    "package: weight (g)": "package_weight_g",
    "item: weight (g)": "item_weight_g",

    "one time coupon: absolute": "coupon_abs",
    "one time coupon: percentage": "coupon_pct",
    "business discount: percentage": "business_discount_pct",
}

PRICE_COLS = [
    "buybox_current","buybox_30d_avg","buybox_90d_avg","buybox_180d_avg","buybox_365d_avg",
    "buybox_lowest","buybox_highest",
    "amazon_current","amazon_30d_avg","amazon_90d_avg","amazon_180d_avg","amazon_365d_avg",
    "amazon_lowest","amazon_highest",
    "new_current","new_30d_avg","new_90d_avg","new_180d_avg","new_365d_avg",
    "new_lowest","new_highest",
    "list_price_current","competitive_price_threshold","suggested_lower_price",
    "new_3p_fba_current","new_3p_fbm_current",
]

PCT_COLS = [
    "sales_rank_30d_drop_pct","sales_rank_90d_drop_pct",
    "buybox_30d_drop_pct",
    "buybox_pct_amz_30d","buybox_pct_amz_90d","buybox_pct_amz_180d","buybox_pct_amz_365d",
    "referral_fee_pct","coupon_pct","business_discount_pct",
]

INT_COLS = [
    "sales_rank_current","sales_rank_30d_avg","sales_rank_90d_avg","sales_rank_180d_avg","sales_rank_365d_avg",
    "sales_rank_drops_30d","sales_rank_drops_90d",
    "bought_past_month","buybox_90d_oos",
    "buybox_winner_cnt_30d","buybox_winner_cnt_90d",
    "total_offer_count","new_offer_count_current","new_offer_count_30d_avg","used_offer_count_current",
    "variation_count","package_volume_cm3","package_length_cm","package_width_cm","package_height_cm",
    "package_weight_g","item_weight_g",
]

DEFAULT_VAT = {
    "IT": 0.22, "DE": 0.19, "FR": 0.20, "ES": 0.21, "NL": 0.21, "BE": 0.21,
    "AT": 0.20, "PL": 0.23, "SE": 0.25, "DK": 0.25, "IE": 0.23, "PT": 0.23,
    "UK": 0.20,
}

REFERRAL_FEE_DEFAULT = 0.15
FBM_FLAT_EUR = 4.00

PRICE_COL_BUY_CANDIDATES = ["new_current","buybox_current"]
PRICE_COL_SELL = "buybox_current"
