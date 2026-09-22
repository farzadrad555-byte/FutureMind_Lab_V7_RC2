"""
V98.15 — TRON USDT PAYMENT CONFIRM ADAPTER
CANDIDATE REPAIR — FAIL-CLOSED

Contract:
    verified
    server_verified
    ref_id
    confirmations
    confirmations_required
    reason
    actual_amount
    expected_amount

Safety:
    REAL_PAYMENT_ENABLED = False
    BLOCKCHAIN_RPC_ENABLED = False
    WALLET_API_ENABLED = False
    PAYMENT_BROADCAST = False
    PRODUCTION_WRITE = False
    ACTIVATION = False

This adapter performs no payment, broadcast, token creation,
gateway activation, or production write by itself.
"""

from pathlib import Path
import importlib.util


REAL_PAYMENT_ENABLED = False
BLOCKCHAIN_RPC_ENABLED = False
WALLET_API_ENABLED = False
PAYMENT_BROADCAST = False
PRODUCTION_WRITE = False
ACTIVATION = False

ASSET = "USDT"
NETWORK = "TRC20"


def _fail(
    reason,
    ref_id=None,
    confirmations=None,
    confirmations_required=None,
    actual_amount=None,
    expected_amount=None,
):
    result = {
        "verified": False,
        "server_verified": False,
        "ref_id": ref_id,
        "confirmations": confirmations,
        "confirmations_required": confirmations_required,
        "reason": reason,
        "actual_amount": actual_amount,
        "expected_amount": expected_amount,
    }
    return result


def _normalize_result(result, tx_hash, expected_amount, confirmations_required):
    """
    Normalize the underlying verifier result into the complete
    payment_confirm contract.

    Important:
    A missing success field can NEVER be converted into success.
    """

    if not isinstance(result, dict):
        return _fail("INVALID_VERIFIER_RESULT")

    verified = result.get("verified") is True
    server_verified = result.get("server_verified") is True

    if not verified or not server_verified:
        return _fail(
            str(result.get("reason") or "VERIFICATION_FAILED"),
            actual_amount=result.get("actual_amount"),
            expected_amount=result.get(
                "expected_amount",
                str(expected_amount),
            ),
        )

    ref_id = result.get("ref_id")

    # ref_id must come from the verifier / on-chain txID.
    # Never manufacture a local fake reference.
    if not ref_id:
        return _fail("REF_ID_MISSING")

    confirmations = result.get("confirmations")

    if confirmations is None:
        return _fail("CONFIRMATIONS_MISSING")

    confirmations_required_result = result.get(
        "confirmations_required",
        confirmations_required,
    )

    if confirmations_required_result is None:
        return _fail("CONFIRMATIONS_REQUIRED_MISSING")

    try:
        confirmations = int(confirmations)
        confirmations_required_result = int(
            confirmations_required_result
        )
    except (TypeError, ValueError):
        return _fail("INVALID_CONFIRMATION_DATA")

    if confirmations < confirmations_required_result:
        return _fail("INSUFFICIENT_CONFIRMATIONS")

    return {
        "verified": True,
        "server_verified": True,
        "ref_id": str(ref_id),
        "confirmations": confirmations,
        "confirmations_required": (
            confirmations_required_result
        ),
        "reason": str(
            result.get("reason") or "VERIFIED_ON_CHAIN"
        ),
        "actual_amount": str(
            result.get("actual_amount", expected_amount)
        ),
        "expected_amount": str(
            result.get("expected_amount", expected_amount)
        ),
    }


def verify_crypto_confirmation(
    payment_data,
    tx_hash,
    expected_wallet,
    expected_amount,
    confirmations_required=1,
):
    """
    Adapter contract for payment_confirm.

    This layer remains fail-closed while the real blockchain
    verifier remains responsible for on-chain verification.
    """

    if not isinstance(payment_data, dict):
        return _fail("INVALID_PAYMENT_DATA")

    if not tx_hash:
        return _fail("MISSING_TX_HASH")

    if not expected_wallet:
        return _fail("MISSING_RECIPIENT")

    if expected_amount is None:
        return _fail("MISSING_EXPECTED_AMOUNT")

    if confirmations_required < 1:
        return _fail("INVALID_CONFIRMATION_REQUIREMENT")

    supplied_asset = (
        payment_data.get("asset")
        or payment_data.get("currency")
    )

    supplied_network = payment_data.get("network")

    if supplied_asset and supplied_asset != ASSET:
        return _fail("ASSET_MISMATCH")

    if supplied_network and supplied_network != NETWORK:
        return _fail("NETWORK_MISMATCH")

    # ----------------------------------------------------------
    # FAIL-CLOSED SAFETY GATES
    # ----------------------------------------------------------
    if not BLOCKCHAIN_RPC_ENABLED:
        return _fail("BLOCKCHAIN_RPC_DISABLED")

    if WALLET_API_ENABLED:
        return _fail("WALLET_API_NOT_ALLOWED")

    if PAYMENT_BROADCAST:
        return _fail("PAYMENT_BROADCAST_NOT_ALLOWED")

    if PRODUCTION_WRITE:
        return _fail("PRODUCTION_WRITE_NOT_ALLOWED")

    if ACTIVATION:
        return _fail("ACTIVATION_NOT_ALLOWED")

    # ----------------------------------------------------------
    # LOAD VERIFIER SOURCE
    #
    # Candidate adapter targets the versioned V5 verifier.
    # No fallback to the obsolete V98_2 verifier.
    # ----------------------------------------------------------
    root = Path(__file__).resolve().parent.parent

    verifier_candidates = [
        root / "tron_usdt_verifier_v5_candidate_20260830_060624.py",
        root / "tron_usdt_verifier_v4_candidate.py",
    ]

    verifier_path = None

    for candidate in verifier_candidates:
        if candidate.exists():
            verifier_path = candidate
            break

    if verifier_path is None:
        return _fail("VERIFIER_SOURCE_NOT_FOUND")

    spec = importlib.util.spec_from_file_location(
        "tron_usdt_verifier_candidate",
        verifier_path,
    )

    if spec is None or spec.loader is None:
        return _fail("VERIFIER_LOAD_FAILED")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    verifier = getattr(
        module,
        "verify_tron_usdt_payment",
        None,
    )

    if verifier is None:
        return _fail("VERIFIER_NOT_FOUND")

    # ----------------------------------------------------------
    # UNDERLYING VERIFIER CALL
    # ----------------------------------------------------------
    result = verifier(
        tx_hash=tx_hash,
        expected_wallet=expected_wallet,
        expected_amount=expected_amount,
        confirmations_required=confirmations_required,
        blockchain_rpc_enabled=BLOCKCHAIN_RPC_ENABLED,
        activation=ACTIVATION,
    )

    # ----------------------------------------------------------
    # NORMALIZE INTO COMPLETE SUCCESS CONTRACT
    # ----------------------------------------------------------
    return _normalize_result(
        result,
        tx_hash,
        expected_amount,
        confirmations_required,
    )
