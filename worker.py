"""
import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from activities import OrderActivities
from shared import PROCESS_ORDER_TASK_QUEUE_NAME
from workflows import ProcessOrder


async def main() -> None:
    client: Client = await Client.connect("localhost:7233", namespace="default")
    # Run the worker
    activities = OrderActivities()

    worker: Worker = Worker(
        client,
        task_queue=PROCESS_ORDER_TASK_QUEUE_NAME,
        workflows=[ProcessOrder],
        activities=[activities.check_inventory, activities.process_payment, \
                    activities.ship_package, activities.notify_customer, \
                    activities.refund_payment, activities.restock_items],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
"""