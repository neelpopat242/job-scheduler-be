import time
import random
import requests

API_BASE_URL = "http://127.0.0.1:5000"
POLL_INTERVAL_SECONDS = 2
LEASE_DURATION_SECONDS = 300


def poll_job():
    response = requests.post(
        f"{API_BASE_URL}/jobs/poll",
        json={"leaseDurationSeconds": LEASE_DURATION_SECONDS},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return None


def ack_job(job_id):
    requests.post(f"{API_BASE_URL}/jobs/{job_id}/ack", timeout=10)
    print(f"Job {job_id} completed")


def fail_job(job_id, error_message):
    requests.post(
        f"{API_BASE_URL}/jobs/{job_id}/fail",
        json={"error": error_message},
        timeout=10
    )
    print(f"Job {job_id} failed: {error_message}")


def process_job(job):
    print(f"Processing job {job.get('jobId')} - {job.get('name')}")
    time.sleep(random.uniform(1, 5))
    return True


def run_worker():
    print("Worker started")

    while True:
        job = poll_job()

        if not job:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        job_id = job.get("jobId")
        print(f"Leased job: {job_id}")

        if process_job(job):
            ack_job(job_id)
        else:
            fail_job(job_id, "Processing failed")


if __name__ == "__main__":
    run_worker()
