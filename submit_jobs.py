import random
import requests

API_BASE_URL = "http://127.0.0.1:5000"

JOB_NAMES = [
    "process-image",
    "send-email",
    "generate-report",
    "sync-data",
    "cleanup-files",
]


def submit_job():
    name = random.choice(JOB_NAMES)
    response = requests.post(
        f"{API_BASE_URL}/jobs",
        json={
            "name": name,
            "description": f"Auto-generated {name} job",
            "metadata": {"priority": random.randint(1, 5)}
        },
        timeout=10
    )
    if response.status_code == 201:
        data = response.json()
        print(f"Submitted: {data['jobId'][:8]}... | {name}")
    else:
        print(f"Failed to submit job: {response.text}")


def get_metrics():
    response = requests.get(f"{API_BASE_URL}/jobs/metadata", timeout=10)
    if response.status_code == 200:
        counts = response.json()["counts"]
        print(f"\n--- Metrics ---")
        print(f"PENDING: {counts['PENDING']}")
        print(f"RUNNING: {counts['RUNNING']}")
        print(f"DONE:    {counts['DONE']}")
        print(f"FAILED:  {counts['FAILED']}")
        print(f"TOTAL:   {counts['total']}")


if __name__ == "__main__":
    num_jobs = 10
    print(f"Submitting {num_jobs} random jobs...\n")
    
    for _ in range(num_jobs):
        submit_job()
    
    get_metrics()


