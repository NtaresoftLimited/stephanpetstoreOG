# -*- coding: utf-8 -*-
import json
import logging
import os
import sqlite3
import tempfile
import threading
import time

_logger = logging.getLogger(__name__)

# Use Linux kernel RAM filesystem (/dev/shm) so all Odoo workers share the exact same sub-millisecond RAM cache
_SHM_DIR = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else tempfile.gettempdir()
_CACHE_DB_PATH = os.path.join(_SHM_DIR, "stephans_odoo20_shared_cache.sqlite")

_LOCAL_LOCK = threading.RLock()
_L1_MEMORY = {}
_L1_LAST_VERSION_CHECK = 0.0
_L1_KNOWN_VERSION = "v1"

# Default TTLs per architectural specification
TTL_SEARCH_SECONDS = 600       # 10 minutes for search queries
TTL_BRAND_SECONDS = 900        # 15 minutes for brand/category pages
TTL_HOMEPAGE_SECONDS = 900     # 15 minutes for homepage product groups


def _get_conn():
    conn = sqlite3.connect(_CACHE_DB_PATH, timeout=5.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            cache_version TEXT NOT NULL,
            payload TEXT NOT NULL,
            product_tags TEXT NOT NULL,
            expires_at REAL NOT NULL,
            created_at REAL NOT NULL
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_meta (
            meta_key TEXT PRIMARY KEY,
            meta_value TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_ns_ver ON cache_entries (namespace, cache_version);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries (expires_at);")
    return conn


def get_cache_version(env=None):
    """Return active cache version string. Incrementing this immediately invalidates all cached entries."""
    global _L1_LAST_VERSION_CHECK, _L1_KNOWN_VERSION
    now = time.time()
    if now - _L1_LAST_VERSION_CHECK < 2.0:
        return _L1_KNOWN_VERSION

    with _LOCAL_LOCK:
        try:
            conn = _get_conn()
            cur = conn.execute("SELECT meta_value FROM cache_meta WHERE meta_key = 'cache_version'")
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                if row[0] != _L1_KNOWN_VERSION:
                    _L1_MEMORY.clear()
                _L1_KNOWN_VERSION = str(row[0])
                _L1_LAST_VERSION_CHECK = now
                return _L1_KNOWN_VERSION
        except Exception as e:
            _logger.debug("Shared cache version check fallback: %s", e)

        if env is not None:
            try:
                ver = env["ir.config_parameter"].sudo().get_param("stephans.cache_version", "v1")
                _L1_KNOWN_VERSION = str(ver or "v1")
                _L1_LAST_VERSION_CHECK = now
                return _L1_KNOWN_VERSION
            except Exception:
                pass
        return _L1_KNOWN_VERSION


def bump_cache_version(env=None):
    """Atomically increment the shared cache version for immediate rollback across all workers."""
    global _L1_KNOWN_VERSION, _L1_LAST_VERSION_CHECK
    now = time.time()
    new_ver = f"v{int(now * 1000)}"
    with _LOCAL_LOCK:
        _L1_MEMORY.clear()
        _L1_KNOWN_VERSION = new_ver
        _L1_LAST_VERSION_CHECK = now
        try:
            conn = _get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO cache_meta (meta_key, meta_value, updated_at) VALUES ('cache_version', ?, ?)",
                (new_ver, now),
            )
            conn.execute("DELETE FROM cache_entries;")
            conn.close()
        except Exception as e:
            _logger.warning("Failed to bump shared cache version in sqlite: %s", e)

        if env is not None:
            try:
                env["ir.config_parameter"].sudo().set_param("stephans.cache_version", new_ver)
            except Exception:
                pass
    return new_ver


def is_anonymous_cacheable(req):
    """Strictly verify that a request is anonymous and does not involve carts, checkout, portal, or auth."""
    if not req:
        return True
    try:
        httpreq = getattr(req, "httprequest", None)
        if httpreq:
            path = (httpreq.path or "").lower()
            forbidden_prefixes = (
                "/shop/cart",
                "/shop/checkout",
                "/shop/payment",
                "/shop/address",
                "/shop/confirm_order",
                "/my",
                "/web/login",
                "/web/session",
                "/paw_points",
            )
            if any(path.startswith(p) for p in forbidden_prefixes):
                return False

        session = getattr(req, "session", None)
        if session:
            # Never cache if customer has an active sale order in session
            if session.get("sale_order_id"):
                return False
            # Never cache if customer has a custom pricelist override in session
            if session.get("website_sale_current_pl"):
                return False
            uid = session.get("uid")
            if uid:
                website = getattr(req, "website", None)
                public_uid = website.user_id.id if (website and getattr(website, "user_id", None)) else None
                if public_uid and uid != public_uid:
                    return False
                elif not public_uid and uid not in (False, None, 4):  # 4 is standard Odoo public user ID
                    return False
    except Exception:
        return False
    return True


def get_cached(namespace, key, env=None):
    """Fetch an entry from the shared cross-worker cache if valid and unexpired."""
    ver = get_cache_version(env)
    full_key = f"{ver}:{namespace}:{key}"
    now = time.time()

    with _LOCAL_LOCK:
        l1_item = _L1_MEMORY.get(full_key)
        if l1_item and l1_item["expires_at"] > now:
            return l1_item["data"]
        elif l1_item:
            _L1_MEMORY.pop(full_key, None)

    try:
        conn = _get_conn()
        cur = conn.execute(
            "SELECT payload, expires_at FROM cache_entries WHERE cache_key = ? AND cache_version = ?",
            (full_key, ver),
        )
        row = cur.fetchone()
        conn.close()
        if row:
            payload_str, expires_at = row
            if expires_at > now:
                data = json.loads(payload_str)
                with _LOCAL_LOCK:
                    _L1_MEMORY[full_key] = {"data": data, "expires_at": expires_at}
                return data
    except Exception as e:
        _logger.debug("Shared cache read error for %s: %s", full_key, e)

    return None


def set_cached(namespace, key, data, ttl=600, product_ids=None, env=None):
    """Store an anonymous response in the shared cross-worker cache tagged with product IDs."""
    ver = get_cache_version(env)
    full_key = f"{ver}:{namespace}:{key}"
    now = time.time()
    expires_at = now + float(ttl)

    tags_str = "|"
    if product_ids:
        clean_ids = sorted({int(pid) for pid in product_ids if pid})
        if clean_ids:
            tags_str = "|" + "|".join(str(pid) for pid in clean_ids) + "|"

    payload_str = json.dumps(data)

    with _LOCAL_LOCK:
        _L1_MEMORY[full_key] = {"data": data, "expires_at": expires_at, "tags": tags_str}
        # Bound L1 memory size
        if len(_L1_MEMORY) > 1000:
            expired = [k for k, v in _L1_MEMORY.items() if v["expires_at"] <= now]
            for k in expired:
                _L1_MEMORY.pop(k, None)

    try:
        conn = _get_conn()
        conn.execute(
            """
            INSERT OR REPLACE INTO cache_entries
            (cache_key, namespace, cache_version, payload, product_tags, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (full_key, namespace, ver, payload_str, tags_str, expires_at, now),
        )
        # Opportunistic cleanup of expired entries
        conn.execute("DELETE FROM cache_entries WHERE expires_at <= ?", (now,))
        conn.close()
    except Exception as e:
        _logger.debug("Shared cache write error for %s: %s", full_key, e)


def invalidate_product_cache(product_ids, env=None):
    """Invalidate ONLY cache entries containing the specified product ID(s) across all workers."""
    if not product_ids:
        return
    if isinstance(product_ids, int):
        product_ids = [product_ids]

    clean_ids = [int(pid) for pid in product_ids if pid]
    if not clean_ids:
        return

    with _LOCAL_LOCK:
        keys_to_remove = []
        for k, v in _L1_MEMORY.items():
            tags = v.get("tags", "")
            if any(f"|{pid}|" in tags for pid in clean_ids) or ":search_api:" in k:
                keys_to_remove.append(k)
        for k in keys_to_remove:
            _L1_MEMORY.pop(k, None)

    try:
        conn = _get_conn()
        # Product tags cannot identify an old cached query that did not yet
        # contain a newly matching product. Clear the small search namespace
        # so search changes become visible across all workers immediately.
        conn.execute("DELETE FROM cache_entries WHERE namespace = ?", ("search_api",))
        for pid in clean_ids:
            tag_pattern = f"%|{pid}|%"
            conn.execute("DELETE FROM cache_entries WHERE product_tags LIKE ?", (tag_pattern,))
        conn.close()
        _logger.info("Invalidated shared cache entries for product IDs: %s", clean_ids)
    except Exception as e:
        _logger.warning("Shared cache invalidation error for products %s: %s", clean_ids, e)
