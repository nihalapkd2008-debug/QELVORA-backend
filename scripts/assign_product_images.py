
from collections import defaultdict

from django.db import transaction

from products.models import Product

# ==================================================
# QELVORA - PRODUCT IMAGE MAPPING
# One unique image URL for every product ID.
# ==================================================

PHOTO_BY_ID = {
    # CLOTHING
    1: "photo-1529139574466-a303027c1d8b",
    5: "photo-1483985988355-763728e1935b",
    6: "photo-1515886657613-9f3515b0c78f",
    7: "photo-1503342217505-b0a15ec3261c",
    8: "photo-1539109136881-3be0616acf4b",
    9: "photo-1556821840-3a63f95609a7",
    10: "photo-1551488831-00ddcb6c6bd3",
    11: "photo-1598033129183-c4f50c736f10",
    12: "photo-1542272604-787c3835535d",
    13: "photo-1517438476312-10d79c077509",
    14: "photo-1515372039744-b8f02a3ae446",
    15: "photo-1490481651871-ab68de25d43d",
    16: "photo-1485230895905-ec40ba36b9bc",
    17: "photo-1591047139829-d91aecb6caea",
    18: "photo-1593032465175-481ac7f401a0",
    19: "photo-1512436991641-6745cdb1723f",

    # BAGS
    2: "photo-1548036328-c9fa89d128fa",
    20: "photo-1584917865442-de89df76afd3",
    21: "photo-1590874103328-eac38a683ce7",
    22: "photo-1566150905458-1bf1fc113f0d",
    23: "photo-1553062407-98eeb64c6a62",
    24: "photo-1622560480654-d96214fdc887",
    25: "photo-1553062407-98eeb64c6a63",
    26: "photo-1591561954557-26941169b49e",
    27: "photo-1547949003-9792a18a2601",
    28: "photo-1594223274512-ad4803739b7c",

    # FOOTWEAR
    3: "photo-1543163521-1bf539c55dd2",
    29: "photo-1549298916-b41d501d3772",
    30: "photo-1460353581641-37baddab0fa2",
    31: "photo-1600185365483-26d7a4cc7519",
    32: "photo-1614252369475-531eba835eb1",
    33: "photo-1562273138-f46be4ebdf33",
    34: "photo-1515347619252-60a4bf4fff4f",
    35: "photo-1542291026-7eec264c27ff",
    36: "photo-1608256246200-53e635b5b65f",
    37: "photo-1535043934128-cf0b28d52f95",

    # WATCHES
    4: "photo-1523275335684-37898b6baf30",
    38: "photo-1524592094714-0f0654e20314",
    39: "photo-1539874754764-5a96559165b0",
    40: "photo-1524805444758-089113d48a6d",
    41: "photo-1508685096489-7aacd43bd3b1",
    42: "photo-1434056886845-dac89ffe9b56",
    43: "photo-1547996160-81dfa63595aa",

    # JEWELRY
    44: "photo-1617038220319-276d3cfab638",
    45: "photo-1535632066927-ab7c9ab60908",
    46: "photo-1611652022419-a9419f74343d",
    47: "photo-1605100804763-247f67b3557e",
    48: "photo-1599643478518-a784e5dc4c8f",

    # ACCESSORIES
    49: "photo-1624222247344-550fb8d4a9f7",
    50: "photo-1627123424574-724758594e93",
    51: "photo-1511499767150-a48a237f0083",
    52: "photo-1517841905240-472988babdf9",
    53: "photo-1601924994987-3a1e6d2f5f0f",
    54: "photo-1521369909029-2afed882baee",
    55: "photo-1553062407-98eeb64c6a64",
}


# ==================================================
# BUILD IMAGE URLS
# ==================================================

IMAGE_BY_ID = {
    product_id: (
        f"https://images.unsplash.com/{photo_id}"
        "?auto=format&fit=crop&w=900&q=85"
    )
    for product_id, photo_id in PHOTO_BY_ID.items()
}


# ==================================================
# VALIDATION - DO NOT UPDATE IF SOMETHING IS WRONG
# ==================================================

if len(IMAGE_BY_ID) != 55:
    raise ValueError(
        f"Expected 55 mappings, found {len(IMAGE_BY_ID)}"
    )

url_to_ids = defaultdict(list)

for product_id, image_url in IMAGE_BY_ID.items():
    url_to_ids[image_url].append(product_id)

duplicates = {
    url: ids
    for url, ids in url_to_ids.items()
    if len(ids) > 1
}

if duplicates:
    print("Duplicate URLs found:")
    for url, ids in duplicates.items():
        print(f"{ids}: {url}")

    raise ValueError("Fix duplicate image URLs before updating.")


existing_ids = set(
    Product.objects.filter(
        id__in=IMAGE_BY_ID.keys()
    ).values_list("id", flat=True)
)

missing_ids = set(IMAGE_BY_ID.keys()) - existing_ids

if missing_ids:
    raise ValueError(
        f"Products not found: {sorted(missing_ids)}"
    )


# ==================================================
# DATABASE UPDATE - IMAGE FIELD ONLY
# ==================================================

with transaction.atomic():
    for product_id, image_url in IMAGE_BY_ID.items():
        Product.objects.filter(
            id=product_id
        ).update(image=image_url)


# ==================================================
# FINAL REPORT
# ==================================================

total = Product.objects.count()

with_images = Product.objects.exclude(
    image__isnull=True
).exclude(image="").count()

without_images = Product.objects.filter(
    image__isnull=True
).count() + Product.objects.filter(image="").count()

print("\n========== QELVORA IMAGE REPORT ==========")
print("Mappings:", len(IMAGE_BY_ID))
print("Unique URLs:", len(set(IMAGE_BY_ID.values())))
print("Total products:", total)
print("Products with images:", with_images)
print("Products without images:", without_images)
print("==========================================")
