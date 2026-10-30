import re

def update_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = content
    for pattern, repl in replacements:
        if isinstance(pattern, str):
            if pattern not in modified:
                print(f"WARNING: '{pattern[:40]}...' not found in {filepath}")
            modified = modified.replace(pattern, repl)
        else: # regex
            modified, count = pattern.subn(repl, modified)
            if count == 0:
                print(f"WARNING: Regex pattern not matched in {filepath}")
    
    if modified != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f"Successfully updated: {filepath}")
    else:
        print(f"No changes made to: {filepath}")

# 1. CartItem.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\CartItem.tsx",
    [
        ("<StockBadge productId={item.productId} stock={currentStock} />", "")
    ]
)

# 2. ProductInfo.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\ProductInfo.tsx",
    [
        (
            re.compile(r'\{currentStock > 0 \? \(\s*<Badge[^>]*>\s*In Stock\s*</Badge>\s*\) : \(\s*<Badge[^>]*>\s*Out of Stock\s*</Badge>\s*\)\}', re.MULTILINE),
            ""
        ),
        (
            "onClick={() => setQuantity(prev => (currentStock > prev ? prev + 1 : prev))}",
            "onClick={() => setQuantity(prev => prev + 1)}"
        )
    ]
)

# 3. QuickViewModal.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\QuickViewModal.tsx",
    [
        (
            re.compile(r'\{/\* Stock Status \*/\}\s*<div className="mt-4">.*?</div>', re.DOTALL),
            ""
        ),
        (
            "Math.min(stock, q + 1)",
            "q + 1"
        ),
        (
            "disabled={isOutOfStock}",
            ""
        ),
        (
            '{isOutOfStock ? "Out of Stock" : "Add to Cart"}',
            '"Add to Cart"'
        ),
        (
            "const isOutOfStock = stock <= 0;",
            "const isOutOfStock = false;"
        )
    ]
)

# 4. ProductCardWidget.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\chat\ProductCardWidget.tsx",
    [
        (
            re.compile(r'\{\(isOutOfStock \|\| isLowStock\) && \(.*?</span>\s*\)\}', re.DOTALL),
            ""
        )
    ]
)

# 5. ProductCard.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\ProductCard.tsx",
    [
        (
            """    if (isOutOfStock) {
      toast.error("Item is currently out of stock");
      return;
    }""",
            ""
        ),
        (
            "disabled={isOutOfStock}",
            ""
        ),
        (
            "const isOutOfStock = stock <= 0;",
            "const isOutOfStock = false;"
        )
    ]
)

# 6. BrandProductCard.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\BrandProductCard.tsx",
    [
        (
            """    if (isOutOfStock) {
      toast.error("Item is currently out of stock");
      return;
    }""",
            ""
        ),
        (
            "disabled={isOutOfStock}",
            ""
        ),
        (
            "const isOutOfStock = stock <= 0;",
            "const isOutOfStock = false;"
        )
    ]
)

# 7. AddToCartButton.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\AddToCartButton.tsx",
    [
        (
            """  // Out of stock
  if (isOutOfStock) {
    return (
      <Button
        disabled
        variant="secondary"
        className={cn("h-11 w-full", className)}
      >
        Out of Stock
      </Button>
    );
  }""",
            ""
        ),
        (
            "if (quantityInCart < stock) {\n      updateQuantity(productId, quantityInCart + 1);\n    }",
            "updateQuantity(productId, quantityInCart + 1);"
        ),
        (
            "disabled={isAtMax}",
            ""
        ),
        (
            "const isOutOfStock = stock <= 0;",
            "const isOutOfStock = false;"
        ),
        (
            "const isAtMax = quantityInCart >= stock;",
            "const isAtMax = false;"
        )
    ]
)

# 8. ProductInfoSkeleton.tsx
update_file(
    r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\ProductInfoSkeleton.tsx",
    [
        (
            """      {/* Stock Badge */}
      <Skeleton className="h-6 w-20" />""",
            ""
        )
    ]
)
