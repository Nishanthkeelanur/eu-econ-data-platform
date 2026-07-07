"""Billing kill-switch: detaches billing from the project when the budget
is exhausted, which immediately stops all billable GCP services.

Triggered by Pub/Sub messages from the Cloud Billing budget. Messages
arrive every ~20-30 min with the current spend; we only act when the
accumulated cost reaches the budget amount.
"""

import base64
import json
import os

import functions_framework
from googleapiclient import discovery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]


@functions_framework.cloud_event
def stop_billing(cloud_event):
    payload = json.loads(
        base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    )
    cost = payload.get("costAmount", 0)
    budget = payload.get("budgetAmount", 0)

    if cost < budget:
        print(f"OK: cost {cost} below kill threshold {budget}")
        return

    billing = discovery.build("cloudbilling", "v1", cache_discovery=False)
    name = f"projects/{PROJECT_ID}"
    info = billing.projects().getBillingInfo(name=name).execute()
    if not info.get("billingEnabled"):
        print("Billing already disabled - nothing to do")
        return

    # Detaching the billing account stops Cloud SQL, Functions, etc.
    # Re-enable manually in the console if this was a false alarm.
    billing.projects().updateBillingInfo(
        name=name, body={"billingAccountName": ""}
    ).execute()
    print(f"KILL SWITCH FIRED: cost {cost} >= {budget}; billing detached from {PROJECT_ID}")
