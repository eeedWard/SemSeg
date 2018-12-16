

# Select the jobs 
    
    SELECT * FROM `aido_evaluation_jobs` WHERE STATUS = 'error' AND stats->"$.msg" like '%with the default driver%' 
    
    SELECT DISTINCT   stats->"$.msg" FROM `aido_evaluation_jobs` WHERE STATUS = 'error' ORDER BY  stats->"$.msg";


Some known problems: 

    UPDATE aido_evaluation_jobs SET status='aborted' WHERE status = 'error' AND stats->"$.msg" like '%with the default driver%';
    
    UPDATE aido_evaluation_jobs SET status='aborted' WHERE status = 'error' AND stats->"$.msg" like '%RequestTimeTooSkewed%';
    
    UPDATE aido_evaluation_jobs SET status='aborted' WHERE status = 'error' AND stats->"$.msg" like '%a prune operation is already%';
    
    
    UPDATE aido_evaluation_jobs SET status='aborted' WHERE status = 'error' AND stats->"$.msg" like '%request canceled while%';
    
    UPDATE aido_evaluation_jobs SET status='aborted' WHERE status = 'error' AND stats->"$.msg" like '%nEndpointConnectionError%';




Error while running Docker Compose:\n\nCould not run ['docker-compose', '-p', 'job6785-1181', 'up', '-d']:\n\n   >  Command '['docker-compose', '-p', 'job6785-1181', 'up', '-d']' returned non-zero exit status 1\n\nstdout | \n\nstderr | Creating network \"job6785-1181_evaluation\" with the default driver\nstderr | Creating job6785-1181_videos_1 ...\nstderr | \u001b[1A\u001b[2K\rCreating job6785-1181_videos_1 ... \u001b[31merror\u001b[0m\r\u001b[1B\nstderr | ERROR: for job6785-1181_videos_1
