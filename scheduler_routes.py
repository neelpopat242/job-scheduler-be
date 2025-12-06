from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from db import mongo
from enums import SchedulerStatus

scheduler_bp = Blueprint('scheduler', __name__)

MAX_RETRIES = 3
LEASE_DURATION_SECONDS = 300


@scheduler_bp.route("/jobs/poll", methods=["POST"])
def poll_job():
    data = request.get_json()
    lease_duration = data.get("leaseDurationSeconds", LEASE_DURATION_SECONDS)

    now = datetime.utcnow()
    lease_expires_at = now + timedelta(seconds=lease_duration)

    job = mongo.db.jobs.find_one_and_update(
        {
            "$or": [
                {"status": SchedulerStatus.PENDING.value},
                {"status": SchedulerStatus.LEASED.value, "leaseExpiresAt": {"$lt": now}}
            ]
        },
        {
            "$set": {
                "status": SchedulerStatus.LEASED.value,
                "leasedAt": now,
                "leaseExpiresAt": lease_expires_at,
                "updatedAt": now
            }
        },
        sort=[("createdAt", 1)],
        return_document=True
    )

    if not job:
        return jsonify({"message": "No jobs available"}), 204

    print(f"JOB_STARTED | jobId={job['jobId']} | retry={job.get('retries')}")

    return jsonify({
        "jobId": job.get("jobId"),
        "name": job.get("name"),
        "description": job.get("description"),
        "data": job.get("data"),
        "status": job.get("status"),
        "retries": job.get("retries"),
        "leaseExpiresAt": lease_expires_at.isoformat(),
    }), 200


@scheduler_bp.route("/jobs/<job_id>/ack", methods=["POST"])
def ack_job(job_id):
    now = datetime.utcnow()

    result = mongo.db.jobs.find_one_and_update(
        {"jobId": job_id, "status": SchedulerStatus.LEASED.value},
        {
            "$set": {
                "status": SchedulerStatus.COMPLETED.value,
                "leasedAt": None,
                "leaseExpiresAt": None,
                "updatedAt": now
            }
        },
        return_document=True
    )

    if not result:
        job = mongo.db.jobs.find_one({"jobId": job_id})
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify({"error": f"Cannot ack job with status '{job.get('status')}'. Job must be LEASED."}), 400

    print(f"JOB_COMPLETED | jobId={job_id}")

    return jsonify({
        "message": "Job completed successfully",
        "jobId": job_id,
        "status": SchedulerStatus.COMPLETED.value
    }), 200


@scheduler_bp.route("/jobs/<job_id>/fail", methods=["POST"])
def fail_job(job_id):
    data = request.get_json() or {}
    error_message = data.get("error", "Unknown error")
    now = datetime.utcnow()

    job = mongo.db.jobs.find_one({"jobId": job_id})

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.get("status") != SchedulerStatus.LEASED.value:
        return jsonify({"error": f"Cannot fail job with status '{job.get('status')}'. Job must be LEASED."}), 400

    current_retries = job.get("retries", 0)
    max_retries = job.get("maxRetries", MAX_RETRIES)
    new_retries = current_retries + 1

    if new_retries >= max_retries:
        mongo.db.jobs.update_one(
            {"jobId": job_id},
            {
                "$set": {
                    "status": SchedulerStatus.DEAD.value,
                    "retries": new_retries,
                    "error": error_message,
                    "leasedAt": None,
                    "leaseExpiresAt": None,
                    "updatedAt": now
                }
            }
        )
        print(f"JOB_FAILED_DLQ | jobId={job_id} | retries={new_retries} | error={error_message}")

        return jsonify({
            "message": "Job moved to Dead Letter Queue",
            "jobId": job_id,
            "status": SchedulerStatus.DEAD.value,
            "retries": new_retries,
            "maxRetries": max_retries
        }), 200
    else:
        mongo.db.jobs.update_one(
            {"jobId": job_id},
            {
                "$set": {
                    "status": SchedulerStatus.PENDING.value,
                    "retries": new_retries,
                    "error": error_message,
                    "leasedAt": None,
                    "leaseExpiresAt": None,
                    "updatedAt": now
                }
            }
        )
        print(f"JOB_FAILED_RETRY | jobId={job_id} | retry={new_retries}/{max_retries} | error={error_message}")

        return jsonify({
            "message": "Job re-queued for retry",
            "jobId": job_id,
            "status": SchedulerStatus.PENDING.value,
            "retries": new_retries,
            "maxRetries": max_retries,
            "remainingRetries": max_retries - new_retries
        }), 200
