"""
token_checker.py - Step 1 of the token rug-pull checker (contract checks only).

Usage:
    python token_checker.py 0xTOKEN_CONTRACT_ADDRESS

Needs:  pip install requests python-dotenv
Key:    ETHERSCAN_API_KEY in your .env file (or in the environment).
Scope:  Ethereum mainnet only (chainid=1).

What it checks (all from the contract itself):
  1. Is the source code published (verified) on Etherscan?
  2. Is it an upgradable proxy (creator can swap the code later)?
  3. Is the owner still in control, or was ownership renounced?
  4. Does the code give the owner risky powers (mint, blacklist, change fees...)?

IMPORTANT: flags are warnings, not proof of a scam. Many legitimate tokens
(for example big stablecoins) also have owner powers. This is only the first
layer; liquidity and creator-wallet checks come in the next steps.
"""
import json
import os
import re
import sys

import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional if the key is already in the environment
    pass

API_URL = "https://api.etherscan.io/v2/api"
CHAIN_ID = "1"
ZERO_ADDRESS = "0x" + "0" * 40
RENOUNCED_FACTOR = 0.25  # owner-only powers matter much less if nobody owns the contract

# ---------------------------------------------------------------------------
# Rules. Every weight is a number of risk points (final score is capped at 100).
# ---------------------------------------------------------------------------

# (id, points, name regex, must_be_owner_only, plain-English reason)
FUNCTION_RULES = [
    ("mint", 20, r"mint", True,
     "The owner can create new tokens whenever they want, which can crash the price."),
    ("blacklist", 20, r"blacklist|blocklist|addbot|setbots?|delbot|blockaddress|banaddress", False,
     "The owner can block wallets from trading or selling (honeypot risk)."),
    ("pause", 10, r"^(pause|unpause|freeze)", True,
     "The owner can freeze all transfers."),
    ("fees", 20, r"^set\w*(tax|fee)|^(update|change)\w*(tax|fee)", True,
     "The owner can change buy/sell fees (they could be raised to trap sellers)."),
    ("limits", 10, r"^set\w*(maxtx|maxtransaction|maxsell|maxwallet|maxbuy)", True,
     "The owner can limit how much you can sell or hold."),
    ("trading_switch", 10, r"^(enabletrading|opentrading|settradingenabled|disabletrading)", False,
     "Trading can be switched on or off by the owner."),
    ("withdraw", 5, r"^(withdraw|rescue|sweep|emergencywithdraw|recover)\w*", True,
     "The owner can pull funds or tokens out of the contract."),
]

# (id, points, owner_dependent, regex on the whole source, plain-English reason)
SOURCE_RULES = [
    ("selfdestruct", 20, False, r"\b(selfdestruct|suicide)\s*\(",
     "The contract can destroy itself."),
    ("delegatecall", 10, False, r"\bdelegatecall\b",
     "It uses delegatecall, which can run other code (check whether it is upgradable)."),
    ("blacklist", 20, True,
     r"mapping\s*\([^)]*\)\s*(public|private|internal)?\s*_?(blacklist\w*|isblacklisted\w*|isbot\w*|bots|blocked\w*)\b",
     "The owner can block wallets from trading or selling (honeypot risk)."),
]

OWNER_DEPENDENT_FUNCTION_IDS = {"mint", "blacklist", "pause", "fees", "limits", "trading_switch", "withdraw"}

FUNC_RE = re.compile(r"function\s+(\w+)\s*\([^)]*\)([^{;]*)[{;]", re.S)


# ---------------------------------------------------------------------------
# Source analysis (no network, so it can be tested on its own)
# ---------------------------------------------------------------------------

def normalize_source(src):
    """Etherscan returns multi-file contracts as JSON (often wrapped in double braces)."""
    s = (src or "").strip()
    if s.startswith("{{") and s.endswith("}}"):
        s = s[1:-1]
    if s.startswith("{"):
        try:
            obj = json.loads(s)
            sources = obj.get("sources", obj)
            parts = [v.get("content", "") for v in sources.values() if isinstance(v, dict)]
            if parts:
                return "\n".join(parts)
        except (ValueError, AttributeError):
            pass
    return src or ""


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def public_functions(src):
    """Yield (lowercase name, is_owner_only) for functions that are not internal/private."""
    for m in FUNC_RE.finditer(src):
        name, mods = m.group(1), m.group(2)
        if re.search(r"\b(internal|private)\b", mods):
            continue
        yield name.lower(), bool(re.search(r"\bonly\w+", mods))


def analyze_source(source, renounced=False):
    """Return {flag_id: {"points": int, "reason": str}} for risky patterns in the code."""
    code = strip_comments(normalize_source(source))
    found = {}

    def add(flag_id, points, reason, owner_dependent):
        if flag_id in found:
            return
        if owner_dependent and renounced:
            points = max(1, round(points * RENOUNCED_FACTOR))
            reason += " (Ownership is renounced, so this is much less risky.)"
        found[flag_id] = {"points": points, "reason": reason}

    for name, owner_only in public_functions(code):
        for flag_id, points, pattern, needs_owner, reason in FUNCTION_RULES:
            if re.search(pattern, name) and (owner_only or not needs_owner):
                add(flag_id, points, reason, flag_id in OWNER_DEPENDENT_FUNCTION_IDS)

    for flag_id, points, owner_dependent, pattern, reason in SOURCE_RULES:
        if re.search(pattern, code, flags=re.I):
            add(flag_id, points, reason, owner_dependent)

    return found


def risk_level(score):
    if score < 25:
        return "LOW"
    if score < 60:
        return "MEDIUM"
    return "HIGH"


# ---------------------------------------------------------------------------
# Etherscan V2 calls (errors are never swallowed)
# ---------------------------------------------------------------------------

def _call(params):
    key = os.getenv("ETHERSCAN_API_KEY")
    if not key:
        raise RuntimeError("ETHERSCAN_API_KEY not found. Put it in your .env file.")
    params = dict(params, chainid=CHAIN_ID, apikey=key)
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_contract(address):
    data = _call({"module": "contract", "action": "getsourcecode", "address": address})
    if str(data.get("status")) != "1":
        raise RuntimeError("Etherscan error: %s - %s" % (data.get("message"), data.get("result")))
    return data["result"][0]


def get_owner(address):
    """Call owner() on the contract. Returns a lowercase address, or None if it cannot be read."""
    data = _call({"module": "proxy", "action": "eth_call", "to": address,
                  "data": "0x8da5cb5b", "tag": "latest"})
    result = data.get("result")
    if not isinstance(result, str) or not result.startswith("0x") or len(result) < 66:
        return None
    return ("0x" + result[-40:]).lower()


# ---------------------------------------------------------------------------
# Main check
# ---------------------------------------------------------------------------

def check_token(address):
    findings = {}
    notes = []

    info = get_contract(address)
    name = info.get("ContractName") or "unknown"
    source = info.get("SourceCode") or ""

    is_proxy = str(info.get("Proxy")) == "1" and info.get("Implementation")
    if is_proxy:
        findings["proxy"] = {"points": 15,
                             "reason": "Upgradable proxy: the creator can swap the contract code later."}
        impl = get_contract(info["Implementation"])
        source = impl.get("SourceCode") or ""
        notes.append("Proxy contract: code was read from implementation %s" % info["Implementation"])

    if not source:
        findings["unverified"] = {"points": 40,
                                  "reason": "Source code is not published, so nobody can check what the contract does."}
        owner_status = "unknown"
    else:
        owner = get_owner(address)
        if owner is None:
            owner_status = "unknown"
            notes.append("Could not read an owner() function, so owner control could not be checked.")
        elif owner == ZERO_ADDRESS:
            owner_status = "renounced"
            notes.append("Ownership is renounced (good sign).")
        else:
            owner_status = "active"
            findings["owner_active"] = {"points": 10,
                                        "reason": "An owner wallet (%s) still controls the contract." % owner}
        findings.update({k: v for k, v in analyze_source(source, renounced=(owner_status == "renounced")).items()
                         if k not in findings})

    score = min(100, sum(f["points"] for f in findings.values()))
    return {"address": address, "name": name, "score": score, "level": risk_level(score),
            "findings": findings, "notes": notes, "owner_status": owner_status}


def print_report(result):
    print("=" * 70)
    print("TOKEN CONTRACT CHECK: %s (%s)" % (result["name"], result["address"]))
    print("=" * 70)
    print("Contract risk score: %d/100  [%s]" % (result["score"], result["level"]))
    print()
    if result["findings"]:
        print("Why:")
        for flag_id, f in sorted(result["findings"].items(), key=lambda kv: -kv[1]["points"]):
            print("  +%-3d %s" % (f["points"], f["reason"]))
    else:
        print("No risky patterns found in the contract code.")
    for note in result["notes"]:
        print("  note: " + note)
    print()
    print("This is only the first layer (contract code). Flags are warnings, not proof of a scam,")
    print("and many legitimate tokens also have owner powers. Liquidity and creator checks come next.")
    print("Data: Powered by Etherscan.io APIs")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not re.fullmatch(r"0x[0-9a-fA-F]{40}", sys.argv[1]):
        print("Usage: python token_checker.py 0xTOKEN_CONTRACT_ADDRESS")
        sys.exit(1)
    try:
        print_report(check_token(sys.argv[1]))
    except RuntimeError as err:
        print("ERROR: %s" % err)
        sys.exit(2)
