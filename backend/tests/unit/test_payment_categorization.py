
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.qbo_client import QBOClient

@pytest.mark.asyncio
async def test_bill_payment_category_ignored(db_session, test_qbo_connection):
    """
    BUG-005 Reproduction:
    Verify that updating a BillPayment with a category_id currently FAILS to include
    it in the payload (the client logic explicitly excludes it).
    """
    with patch('app.services.qbo_client.AuthClient') as MockAuth:
        mock_auth = MagicMock()
        MockAuth.return_value = mock_auth
        
        client = QBOClient(db_session, test_qbo_connection)
    
        with patch.object(client, 'request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"BillPayment": {"Id": "123"}}
            
            await client.update_purchase(
                purchase_id="123",
                category_id="cat_456",
                category_name="Office Expense",
                sync_token="0",
                entity_type="BillPayment"
            )
        
        # Capture payload
        call_args = mock_request.call_args
        assert call_args is not None
        payload = call_args.kwargs.get('json_payload')
        
        print(f"Payload sent: {payload}")

        # Current logic: BillPayment has NO line with AccountRef because QBOClient strips it
        lines = payload.get("Line", [])
        has_account_ref = False
        for line in lines:
            if "BillPaymentLineDetail" in line:
                 if "AccountRef" in line.get("BillPaymentLineDetail", {}):
                     has_account_ref = True
            elif "AccountBasedExpenseLineDetail" in line:
                if "AccountRef" in line.get("AccountBasedExpenseLineDetail", {}):
                     has_account_ref = True

        # Assert Fix: AccountRef should be PRESENT
        assert has_account_ref, "Fix Verification: AccountRef should be present for BillPayment"
