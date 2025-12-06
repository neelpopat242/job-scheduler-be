Job Scheduler API:

A distributed job scheduling system with lease-based polling, automatic retries, and dead letter queue.


Auto-Scaling Workers:

Workers can be scaled based on queue depth from metadata analysis. A controller polls pending job count and adjusts worker replicas . Scale-down requires graceful shutdown—workers must finish current jobs before terminating to avoid orphaned leases.
