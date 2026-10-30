path = r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\components\app\QuickViewModal.tsx"
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('"Add to Cart"', 'Add to Cart')
with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print("Fixed QuickViewModal.tsx")
