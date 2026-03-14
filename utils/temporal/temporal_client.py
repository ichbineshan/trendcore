import asyncio
import logging
import uuid
from datetime import timedelta
from typing import Dict, Any, Optional, Callable, List

from temporalio.client import Client, WorkflowHandle
from temporalio.common import RetryPolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from config.logging import logger
from config.settings import loaded_config


class TemporalClient:
    """
    A generalized Temporal client for managing workflows across different repositories.

    This client provides a comprehensive interface for interacting with Temporal workflows,
    including starting, querying, signaling, and managing workflow lifecycles.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        namespace: str = "default",
        logger_instance: Optional[logging.Logger] = None,
    ):
        """
        Initialize the Temporal client.

        Args:
            host: Temporal server host (defaults to config or localhost:7233)
            namespace: Temporal namespace to use (defaults to "default")
            logger_instance: Custom logger instance (optional)
        """
        self._client = None
        self._host = host or loaded_config.temporal_host
        self._namespace = namespace
        self._logger = logger_instance or logger

    async def get_client(self) -> Client:
        """
        Get or create Temporal client connection.

        Returns:
            Client: Connected Temporal client instance
        """
        if not self._client:
            self._client = await Client.connect(
                target_host=self._host, namespace=self._namespace
            )
            self._logger.info(
                f"Connected to Temporal at {self._host} in namespace {self._namespace}"
            )
        return self._client

    async def start_workflow(
        self,
        workflow_class: Any,
        workflow_method: Callable,
        args: List[Any] = None,
        workflow_id: Optional[str] = None,
        task_queue: str = "default",
        execution_timeout: Optional[timedelta] = None,
        run_timeout: Optional[timedelta] = None,
        task_timeout: Optional[timedelta] = None,
        retry_policy: Optional[RetryPolicy] = None,
        memo: Optional[Dict[str, Any]] = None,
        search_attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start a new workflow execution.

        Args:
            workflow_class: The workflow class to execute
            workflow_method: The workflow method to call (usually workflow_class.run)
            args: Arguments to pass to the workflow (defaults to empty list)
            workflow_id: Unique identifier for the workflow (auto-generated if None)
            task_queue: Task queue name for the workflow
            execution_timeout: Maximum time for entire workflow execution
            run_timeout: Maximum time for a single workflow run
            task_timeout: Maximum time for workflow tasks
            retry_policy: Retry policy for the workflow
            memo: Memo data for the workflow
            search_attributes: Search attributes for workflow discovery

        Returns:
            str: The workflow execution ID

        Raises:
            WorkflowAlreadyStartedError: If workflow with same ID already exists
        """
        client = await self.get_client()
        args = args or []

        if not workflow_id:
            workflow_id = f"{workflow_class.__name__.lower()}-{uuid.uuid4()}"

        try:
            handle = await client.start_workflow(
                workflow_method,
                *args,
                id=workflow_id,
                task_queue=task_queue,
                execution_timeout=execution_timeout,
                run_timeout=run_timeout,
                task_timeout=task_timeout,
                retry_policy=retry_policy,
                memo=memo,
                search_attributes=search_attributes,
            )

            return handle.id

        except WorkflowAlreadyStartedError as e:
            raise e
        except Exception as e:
            raise e

    async def get_workflow_handle(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> WorkflowHandle:
        """
        Get a handle to an existing workflow.

        Args:
            workflow_id: The workflow ID
            run_id: Specific run ID (optional)

        Returns:
            WorkflowHandle: Handle to the workflow
        """
        client = await self.get_client()
        return client.get_workflow_handle(workflow_id, run_id=run_id)

    async def get_workflow_status(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get the status of a workflow.

        Args:
            workflow_id: The workflow ID
            run_id: Specific run ID (optional)

        Returns:
            Dict containing workflow status information
        """
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)
            description = await handle.describe()

            return {
                "workflow_id": workflow_id,
                "run_id": description.run_id,
                "status": description.status.name,
                "start_time": description.start_time,
                "execution_time": description.execution_time,
                "close_time": description.close_time,
                "task_queue": description.task_queue,
                "workflow_type": description.workflow_type,
            }
        except Exception as e:
            raise e

    async def signal_workflow(
        self,
        workflow_id: str,
        signal_name: str,
        args: List[Any] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Send a signal to a running workflow.

        Args:
            workflow_id: The workflow ID
            signal_name: Name of the signal to send
            args: Arguments for the signal (defaults to empty list)
            run_id: Specific run ID (optional)
        """
        args = args or []
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)
            await handle.signal(signal_name, *args)
        except Exception as e:
            raise e

    async def query_workflow(
        self,
        workflow_id: str,
        query_name: str,
        args: List[Any] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """
        Query a workflow for information.

        Args:
            workflow_id: The workflow ID
            query_name: Name of the query
            args: Arguments for the query (defaults to empty list)
            run_id: Specific run ID (optional)

        Returns:
            Query result
        """
        args = args or []
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)
            result = await handle.query(query_name, *args)
            return result
        except Exception as e:
            raise e

    async def cancel_workflow(
        self, workflow_id: str, run_id: Optional[str] = None
    ) -> None:
        """
        Cancel a running workflow.

        Args:
            workflow_id: The workflow ID
            run_id: Specific run ID (optional)
        """
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)
            await handle.cancel()
        except Exception as e:
            raise e

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> None:
        """
        Terminate a workflow immediately.

        Args:
            workflow_id: The workflow ID
            reason: Reason for termination (optional)
            run_id: Specific run ID (optional)
        """
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)
            await handle.terminate(reason=reason)
        except Exception as e:
            raise e

    async def wait_for_workflow_result(
        self,
        workflow_id: str,
        timeout: Optional[timedelta] = None,
        run_id: Optional[str] = None,
    ) -> Any:
        """
        Wait for a workflow to complete and return its result.

        Args:
            workflow_id: The workflow ID
            timeout: Maximum time to wait (optional)
            run_id: Specific run ID (optional)

        Returns:
            Workflow result
        """
        try:
            handle = await self.get_workflow_handle(workflow_id, run_id)

            if timeout:
                result = await asyncio.wait_for(
                    handle.result(), timeout=timeout.total_seconds()
                )
            else:
                result = await handle.result()
            return result
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            raise e

    async def list_workflows(
        self, query: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List workflows based on query criteria.

        Args:
            query: Temporal query string (optional, defaults to all workflows)
            limit: Maximum number of workflows to return

        Returns:
            List of workflow information dictionaries
        """
        try:
            client = await self.get_client()
            workflows = []

            async for workflow in client.list_workflows(query or "", page_size=limit):
                workflows.append(
                    {
                        "workflow_id": workflow.id,
                        "run_id": workflow.run_id,
                        "workflow_type": workflow.workflow_type,
                        "status": workflow.status.name,
                        "start_time": workflow.start_time,
                        "execution_time": workflow.execution_time,
                        "close_time": workflow.close_time,
                        "task_queue": workflow.task_queue,
                    }
                )

                if len(workflows) >= limit:
                    break

            self._logger.info(f"Retrieved {len(workflows)} workflows")
            return workflows
        except Exception as e:
            self._logger.error(f"Failed to list workflows: {str(e)}")
            raise e

    async def close(self) -> None:
        """Close the Temporal client connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._logger.info("Temporal client connection closed")
