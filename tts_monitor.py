#!/usr/bin/env python3
"""
TTS Status Monitor - Check the status of the TTS job queue and workers
"""
import os
import sys
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import FailedJobRegistry
from app.config import settings

def check_redis():
    """Check Redis connection."""
    try:
        r = Redis.from_url(settings.redis_url)
        r.ping()
        return r, True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return None, False

def get_queue_stats(redis_conn):
    """Get queue statistics."""
    try:
        q = Queue(settings.queue_name, connection=redis_conn)
        failed_registry = FailedJobRegistry(queue=q)
        
        # Count workers differently
        worker_keys = redis_conn.smembers('rq:workers:tts')
        worker_count = len(worker_keys) if worker_keys else 0
        
        stats = {
            'queued': len(q),
            'failed': len(failed_registry),
            'workers': worker_count,
            'wip': redis_conn.zcard('rq:wip:tts')
        }
        return stats
    except Exception as e:
        print(f"❌ Failed to get queue stats: {e}")
        return None

def show_recent_jobs(redis_conn, limit=5):
    """Show recent job statuses."""
    try:
        # Get job IDs from failed registry
        failed_jobs = redis_conn.zrange('rq:failed:tts', 0, limit-1)
        
        print(f"\n📋 Recent Jobs (last {limit}):")
        print("-" * 60)
        
        for job_id_bytes in failed_jobs[-limit:]:
            try:
                job_id = job_id_bytes.decode('utf-8') if isinstance(job_id_bytes, bytes) else job_id_bytes
                job = Job.fetch(job_id, connection=redis_conn)
                print(f"Job {job_id[:8]}... | Status: {job.get_status()} | Created: {job.created_at}")
                if hasattr(job, 'meta') and job.meta:
                    total = job.meta.get('total_chunks', '?')
                    processed = job.meta.get('processed_chunks', '?')
                    print(f"  Progress: {processed}/{total} chunks")
            except Exception as e:
                job_display = job_id_bytes[:8] if isinstance(job_id_bytes, bytes) else job_id_bytes[:8]
                print(f"Job {job_display}... | Error fetching details: {e}")
        
        # Also check for any jobs in work-in-progress
        wip_jobs = redis_conn.zrange('rq:wip:tts', 0, -1)
        if wip_jobs:
            print(f"\n⏳ Work-in-Progress Jobs:")
            for wip_id in wip_jobs:
                # Redis returns bytes; decode to str before splitting/printing
                if isinstance(wip_id, bytes):
                    wip_id_str = wip_id.decode('utf-8', errors='replace')
                else:
                    wip_id_str = wip_id
                job_id = wip_id_str.split(':')[0]
                print(f"  {job_id[:8]}...")
                
    except Exception as e:
        print(f"❌ Failed to show recent jobs: {e}")

def clean_stale_data(redis_conn):
    """Clean stale worker registrations and orphaned jobs."""
    try:
        # Clean stale worker registrations
        workers_cleaned = redis_conn.delete('rq:workers:tts')
        
        # Clean orphaned work-in-progress jobs
        wip_jobs = redis_conn.zrange('rq:wip:tts', 0, -1)
        wip_cleaned = 0
        if wip_jobs:
            wip_cleaned = redis_conn.zrem('rq:wip:tts', *wip_jobs)
        
        print(f"🧹 Cleaned {workers_cleaned} worker registrations, {wip_cleaned} orphaned WIP jobs")
        return True
    except Exception as e:
        print(f"❌ Failed to clean stale data: {e}")
        return False

def main():
    """Main function."""
    print("🔍 TTS Status Monitor")
    print("=" * 50)
    
    # Check Redis
    redis_conn, redis_ok = check_redis()
    if not redis_ok:
        sys.exit(1)
    print("✅ Redis connection OK")
    
    # Get queue statistics
    stats = get_queue_stats(redis_conn)
    if stats:
        print(f"\n📊 Queue Statistics:")
        print(f"  Queued jobs: {stats['queued']}")
        print(f"  Failed jobs: {stats['failed']}")
        print(f"  Active workers: {stats['workers']}")
        print(f"  Work-in-progress: {stats['wip']}")
        
        # Status assessment
        if stats['workers'] == 0:
            print("\n⚠️  WARNING: No active workers found!")
            print("   Run 'make worker' to start a worker process")
        elif stats['queued'] > 0:
            print(f"\n✅ {stats['queued']} job(s) waiting to be processed")
        else:
            print("\n✅ System ready - no jobs in queue")
    
    # Show recent jobs
    show_recent_jobs(redis_conn)
    
    # Offer to clean stale data if needed
    if stats and (stats['wip'] > 0 or len(sys.argv) > 1 and sys.argv[1] == '--clean'):
        print(f"\n🧹 Clean stale data? (y/N): ", end='')
        if len(sys.argv) > 1 and sys.argv[1] == '--clean':
            response = 'y'
            print('y (auto-clean)')
        else:
            response = input().lower().strip()
        
        if response in ['y', 'yes']:
            clean_stale_data(redis_conn)

if __name__ == "__main__":
    main()