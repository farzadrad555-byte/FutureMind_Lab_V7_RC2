
from decimal import Decimal
import requests


TRON_API = "https://api.trongrid.io"

USDT_TRC20_CONTRACT = (
    "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
)

USDT_DECIMALS = Decimal("1000000")


def _tron_hex_to_base58(address):
    """
    Normalize TRON event addresses to Base58.
    Accepts Base58, 41-prefixed hex, or 0x-prefixed hex.
    """
    if not address:
        return None

    address = str(address)

    if address.startswith("T"):
        return address

    if address.startswith("0x"):
        address = address[2:]

    if len(address) == 40:
        address = "41" + address

    try:
        raw = bytes.fromhex(address)

        if len(raw) != 21 or raw[0] != 0x41:
            return None

        return _base58check_encode(raw)
    except Exception:
        return None


def _base58check_encode(payload):
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    checksum = __import__("hashlib").sha256(
        __import__("hashlib").sha256(payload).digest()
    ).digest()[:4]

    data = payload + checksum
    number = int.from_bytes(data, "big")
    encoded = ""

    while number:
        number, rem = divmod(number, 58)
        encoded = alphabet[rem] + encoded

    leading_zeroes = len(data) - len(data.lstrip(b"\\x00"))

    return ("1" * leading_zeroes) + (encoded or "1")


def _fail(reason):
    return {
        "verified": False,
        "server_verified": False,
        "reason": reason,
    }


def verify_tron_usdt_payment(
    *,
    tx_hash,
    expected_wallet,
    expected_amount,
    confirmations_required=1,
    blockchain_rpc_enabled=False,
    activation=False,
):
    """
    V5 READ-ONLY TRON/TRC20 verifier candidate.

    This function NEVER authorizes payment unless:
      - required inputs are present
      - RPC is explicitly enabled
      - activation is explicitly enabled
      - transaction is valid
      - TRC20 USDT contract matches
      - recipient matches
      - amount matches
      - confirmation gate passes

    No token creation.
    No order mutation.
    No payment broadcast.
    """

    if not tx_hash:
        return _fail("MISSING_TX_HASH")

    if not expected_wallet:
        return _fail("MISSING_RECIPIENT")

    if expected_amount is None:
        return _fail("MISSING_EXPECTED_AMOUNT")

    if confirmations_required < 1:
        return _fail("INVALID_CONFIRMATION_REQUIREMENT")

    if not blockchain_rpc_enabled:
        return _fail("BLOCKCHAIN_RPC_DISABLED")

    if not activation:
        return _fail("TRON_VERIFIER_NOT_ACTIVATED")

    try:
        tx_url = (
            f"{TRON_API}/wallet/gettransactionbyid"
        )

        tx_response = requests.get(
            tx_url,
            params={"value": tx_hash},
            timeout=15,
        )

        if tx_response.status_code != 200:
            return _fail("RPC_HTTP_ERROR")

        tx = tx_response.json()

    except Exception:
        return _fail("RPC_REQUEST_FAILED")

    if not isinstance(tx, dict):
        return _fail("INVALID_TX_RESPONSE")

    if not tx:
        return _fail("TX_NOT_FOUND")

    tx_id = tx.get("txID")

    if not tx_id:
        return _fail("TX_ID_MISSING")

    # --------------------------------------------------
    # Transaction result/status
    # --------------------------------------------------

    ret = tx.get("ret")

    if isinstance(ret, list) and ret:
        contract_result = ret[0].get("contractRet")

        if contract_result and contract_result != "SUCCESS":
            return _fail("TX_NOT_SUCCESSFUL")

    # --------------------------------------------------
    # TRC20 event lookup
    # --------------------------------------------------

    try:
        event_url = (
            f"{TRON_API}/v1/transactions/"
            f"{tx_id}/events"
        )

        event_response = requests.get(
            event_url,
            params={
                "limit": 200,
                "only_confirmed": "true",
            },
            timeout=15,
        )

        if event_response.status_code != 200:
            return _fail("EVENT_RPC_ERROR")

        event_payload = event_response.json()

    except Exception:
        return _fail("EVENT_REQUEST_FAILED")

    data = event_payload.get("data")

    if not isinstance(data, list):
        return _fail("EVENT_DATA_INVALID")

    transfer = None

    for event in data:
        if not isinstance(event, dict):
            continue

        if event.get("event_name") != "Transfer":
            continue

        result = event.get("result")

        if not isinstance(result, dict):
            continue

        contract = (
            event.get("contract_address")
            or event.get("address")
            or event.get("contract")
            or result.get("contract")
        )

        if contract != USDT_TRC20_CONTRACT:
            continue

        to_address_raw = (
            result.get("to")
            or result.get("_to")
        )

        to_address = _tron_hex_to_base58(to_address_raw)

        if to_address is None:
            to_address = to_address_raw

        value = (
            result.get("value")
            or result.get("_value")
        )

        if to_address != expected_wallet:
            continue

        if value is None:
            continue

        transfer = {
            "contract": contract,
            "to": to_address,
            "value": value,
            "block_number": event.get("block_number"),
        }

        break

    if transfer is None:
        return _fail("USDT_RECIPIENT_NOT_FOUND")

    # --------------------------------------------------
    # Amount verification
    # --------------------------------------------------

    try:
        actual_raw = Decimal(
            str(transfer["value"])
        )

        actual_amount = (
            actual_raw / USDT_DECIMALS
        )

        expected = Decimal(
            str(expected_amount)
        )

    except Exception:
        return _fail("INVALID_AMOUNT_DATA")

    if actual_amount != expected:
        return {
            "verified": False,
            "server_verified": False,
            "reason": "AMOUNT_MISMATCH",
            "actual_amount": str(actual_amount),
            "expected_amount": str(expected),
        }

    # --------------------------------------------------
    # Confirmation gate
    # --------------------------------------------------

    # Candidate boundary:
    # exact confirmation-depth calculation must be
    # completed before production activation.

    # ========================================================
    # V98.15.82 — CONFIRMATION DEPTH CONTRACT
    # ========================================================

    tx_block_raw = (
        tx.get("blockNumber")
        or tx.get("block_number")
        or transfer.get("block_number")
    )

    try:
        tx_block = int(tx_block_raw)
    except (TypeError, ValueError):
        return _fail("TX_BLOCK_NUMBER_MISSING")

    latest_response = requests.get(
        f"{TRON_API}/wallet/getnowblock",
        timeout=10,
    )

    if latest_response.status_code != 200:
        return _fail("LATEST_BLOCK_RPC_HTTP_ERROR")

    try:
        latest_payload = latest_response.json()
    except ValueError:
        return _fail("LATEST_BLOCK_RESPONSE_INVALID")

    latest_block_raw = (
        latest_payload
        .get("block_header", {})
        .get("raw_data", {})
        .get("number")
    )

    try:
        latest_block = int(latest_block_raw)
    except (TypeError, ValueError):
        return _fail("LATEST_BLOCK_NUMBER_MISSING")

    confirmations = latest_block - tx_block + 1

    if confirmations < confirmations_required:
        return _fail("INSUFFICIENT_CONFIRMATIONS")

    # --------------------------------------------------------
    # CANONICAL CRYPTO REFERENCE
    # --------------------------------------------------------
    #
    # ref_id is NOT generated locally.
    # It is the actual on-chain transaction ID returned
    # by the blockchain RPC.
    # --------------------------------------------------------

    ref_id = str(tx_id)

    if not ref_id:
        return _fail("REF_ID_MISSING")

    # --------------------------------------------------------
    # SUCCESS CONTRACT
    # --------------------------------------------------------

    return {
        "verified": True,
        "server_verified": True,
        "reason": "VERIFIED_ON_CHAIN",
        "actual_amount": str(actual_amount),
        "expected_amount": str(expected),
        "ref_id": ref_id,
        "confirmations": confirmations,
        "confirmations_required": confirmations_required,
    }


if __name__ == "__main__":
    result = verify_tron_usdt_payment(
        tx_hash="FORENSIC-FAKE-TX",
        expected_wallet="TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        expected_amount="49",
        confirmations_required=1,
        blockchain_rpc_enabled=False,
        activation=False,
    )

    print(result)

    assert result["verified"] is False
    assert result["server_verified"] is False
