import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify
from db import mongo
from enums import SchedulerStatus, get_client_status

client_bp = Blueprint('client', __name__)

MAX_RETRIES = 3


def format_job_for_client(job):
    return {
        "jobId": job.get("jobId"),
        "name": job.get("name"),
        "description": job.get("description"),
        "status": get_client_status(job.get("status")),
        "error": job.get("error"),
        "createdAt": job.get("createdAt").isoformat() if job.get("createdAt") else None,
        "updatedAt": job.get("updatedAt").isoformat() if job.get("updatedAt") else None,
    }


@client_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"message": "Job API is running"}), 200


@client_bp.route("/jobs", methods=["POST"])
def submit_job():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400
    if "name" not in data:
        return jsonify({"error": "name is required"}), 400

    job_id = str(uuid.uuid4())
    now = datetime.utcnow()

    job = {
        "jobId": job_id,
        "name": data.get("name"),
        "description": data.get("description"),
        "data": data.get("metadata", {}),
        "status": SchedulerStatus.PENDING.value,
        "retries": 0,
        "maxRetries": MAX_RETRIES,
        "error": None,
        "leasedAt": None,
        "leaseExpiresAt": None,
        "createdAt": now,
        "updatedAt": now,
    }

    mongo.db.jobs.insert_one(job)
    print(f"JOB_SUBMITTED | jobId={job_id} | name={job['name']}")

    return jsonify({
        "message": "Job submitted successfully",
        "jobId": job_id,
        "status": get_client_status(job["status"]),
    }), 201


@client_bp.route("/jobs/<job_id>/status", methods=["GET"])
def get_job_status(job_id):
    job = mongo.db.jobs.find_one({"jobId": job_id}, {"_id": 0})

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(format_job_for_client(job)), 200


@client_bp.route("/jobs/metadata", methods=["GET"])
def get_jobs_metadata():
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]

    results = list(mongo.db.jobs.aggregate(pipeline))
    status_counts = {item["_id"]: item["count"] for item in results}

    pending = status_counts.get(SchedulerStatus.PENDING.value, 0)
    running = status_counts.get(SchedulerStatus.LEASED.value, 0)
    done = status_counts.get(SchedulerStatus.COMPLETED.value, 0)
    failed = status_counts.get(SchedulerStatus.DEAD.value, 0)

    return jsonify({
        "counts": {
            "PENDING": pending,
            "RUNNING": running,
            "DONE": done,
            "FAILED": failed,
            "total": pending + running + done + failed
        }
    }), 200
