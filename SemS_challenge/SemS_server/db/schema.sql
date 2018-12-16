SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS aido_log_entries;
DROP TABLE IF EXISTS aido_log_categories;

DROP TABLE IF EXISTS aido_evaluators;
DROP TABLE IF EXISTS aido_evaluation_jobs;
DROP TABLE IF EXISTS aido_submissions;
DROP TABLE IF EXISTS aido_challenges;

DROP TABLE IF EXISTS aido_challenges_evaluation_steps;

CREATE TABLE aido_challenges (
  challenge_id bigint(20) unsigned unique auto_increment primary key,
  queue_name   VARCHAR(128) unique,

  tags JSON not null,

  title        VARCHAR(1000),
  description  VARCHAR(1000),

  protocol     VARCHAR(64),

  scoring      JSON not null,
  transitions  JSON not null,

  # Submissions open
  date_open    datetime                   default NOW(),

  # Submissions closed
  date_close   datetime                   default '2018-12-31',

  admin_aborted bool default false

);


create table aido_challenges_role_assignments (
  role_assignment_id bigint(20) unsigned unique auto_increment primary key,

  user_id            bigint(20) unsigned references wp_users (ID),

  challenge_id       bigint(20) unsigned references aido_challenges (challenge_id),

  # The power to change the evaluation procedure, as in changing the evaluation container
  power_change       bool,

  # The power to grant and revoke permissions to other users for this challenge.
  power_grant        bool,

  # The power to moderate the challenge, as in removing submissions, starting/stopping evaluation jobs,
  # setting priorities, etc.
  power_moderate     bool,

  # The power to see all the submissions, including others
  power_snoop        bool

);

# insert into aido_challenges (challenge_id, queue_name, title, description, protocol, challenge_parameters) values
#   (1,'aido1_luck-v2',
#    'A test of luck (second version).',
#    'Try your luck --- skills not necessary',
#     'p1',
#    '{
#      "protocol": "p1",
#      "container": "andreacensi/aido1_luck-evaluator-v2:2018_08_31_17_05_47"
#    }');
#
# insert into aido_challenges_role_assignments(user_id, challenge_id, power_change, power_moderate, power_snoop) values
#   # Andrea C., luck, change, moderate, snoop
#   (3, 1, true, true, true),
#   # Andrea D., luck, !change, moderate, snoop
#   (443, 1, false, true, true);


CREATE TABLE aido_submissions (
  submission_id      bigint(20) unsigned unique auto_increment primary key,
  user_id            bigint(20) unsigned not null references wp_users (id),

  date_submitted     datetime            not null,
  status             ENUM ('submitted', 'evaluating', 'retired', 'aborted', 'success', 'failed', 'error'),
  last_status_change datetime            not null,
  challenge_id       bigint(20) unsigned not null references aido_challenges (challenge_id),
  # XXX
  parameters         JSON                not null,
  # new fields for next version
  evaluation_parameters JSON not null,

  # was it retired by the user
  user_label         varchar(128),
  user_metadata      JSON not null,
  user_retired bool default false,
  user_priority      int    default 50,

  # was it aborted by the admin
  admin_priority     int    default 50,
  admin_aborted bool default false
);

CREATE TABLE aido_evaluation_generation (
  generation_id  bigint(20) unsigned unique auto_increment primary key,
  submission_id bigint(20) unsigned not null references aido_submissions (submission_id),
  # TODO: seed
  seed bigint(20) unsigned not null
);

CREATE TABLE aido_evaluation_jobs (
  job_id         bigint(20) unsigned unique auto_increment primary key,
  step_id        bigint(20) unsigned not null references aido_challenges_evaluation_steps (step_id),
  submission_id  bigint(20) unsigned not null references aido_submissions (submission_id),
  evaluator_id   bigint(20) unsigned not null references aido_evaluators (evaluator_id),

  generation_id  bigint(20) unsigned references aido_evaluation_generation (generation_id),

  evaluation_parameters JSON not null,
  date_started   datetime not null,
  status         ENUM ('evaluating', 'timeout', 'success', 'failed', 'error', 'aborted'),
  date_completed datetime,
  stats          JSON

);


CREATE TABLE aido_evaluation_jobs_stats (
  score_id bigint(20) unsigned unique auto_increment primary key,
  job_id  bigint(20) unsigned not null references aido_evaluation_jobs(job_id),
  name VARCHAR(64) not null,
#   driven_lanedir_consecutive_median
  value JSON not null
#   # 0 = statistics
#   # 1 = scores
#   importance int unsigned default false,
#   value double not null,
#   comments VARCHAR(2048)
);


CREATE TABLE aido_evaluation_jobs_artefacts (
  artefact_id bigint(20) unsigned unique auto_increment primary key,
  job_id  bigint(20) unsigned not null references aido_evaluation_jobs(job_id),
  rpath VARCHAR(256) not null,
  mime_type VARCHAR(32) not null,
  size int unsigned not null,
  sha256hex VARCHAR(256) not null
);

create table aido_artefacts_s3objects (
  s3object_id  bigint(20) unsigned unique auto_increment primary key,
  sha256hex VARCHAR(256) not null,
  bucket_name VARCHAR(32) not null,
  object_key VARCHAR(1024) not null,
  url VARCHAR(1024) not null
);


create table aido_evaluation_features (
  evaluation_feature_id        bigint(20) unsigned unique auto_increment primary key,
  # url-compatible name
  feature_name                 VARCHAR(25)   not null,
  # very short name
  short                        VARCHAR(32)   not null,
  # long description
  long_md                      VARCHAR(1024) not null,

  # hierarchical organization
  parent_evaluation_feature_id bigint(20) unsigned references aido_evaluation_features (evaluation_feature_id)

);


insert into aido_evaluation_features (evaluation_feature_id, feature_name, short, long_md, parent_evaluation_feature_id)
values (1, 'computation', 'Computation', 'Computational properties', 1),
       (11, 'armv7l', 'arm', 'The machine has an armv7l architecture', 1),
       (12, 'x86_64', 'x86_64', 'The machine has x86_64 architecture', 1),
       (13, 'linux', 'Linux', '', 1),
       (14, 'mac', 'Mac', 'Mac', 1),
       (15, 'gpu', 'gpu available', 'The machine has a GPU available', 1),
       (131, 'cores', 'gpu cores', 'Number of cores available', 13),
       (16, 'nprocessors', 'Number of processors', '', 1),
       (17, 'processor_frequency_mhz', 'Processor frequency (MHz)', '', 1),
       (18, 'processor_free_percent', 'Free % of processors', '', 1),
       (2, 'memory', 'Memory', 'Computational properties', null),
       (21, 'ram_total_mb', 'RAM total (MB)', 'RAM available to the machine (measured in MB)', 2),
       (22, 'ram_available_mb', 'RAM free (MB)', 'RAM available to the machine (measured in MB)', 2),
       (3, 'disk', 'Disk', 'Storage properties', null),
       (31, 'disk_total_mb', 'Disk (MB)', 'Total disk space (measured in MB)', 3),
       (32, 'disk_available_mb', 'Disk available (MB)', 'Available disk space (measured in MB)', 3),
       (4, 'accounts', 'Accounts', 'Accounts required', null),
       (41, 'dockerhub', 'Docker Hub', 'The machine has a dockerhub account configured', 4),
       (5, 'protocols', 'Protocols', 'Protocols implemented by the machine', null),
       (51, 'p1', 'P1', 'The machine implements protocol 1', 5),
       (52, 'p2', 'P2', 'The machine implements protocol 2', 5),
       (6, 'hardware', 'Hardware equipment', '', null),
       (61, 'picamera', 'PI Camera', 'Device has a camera', 6),
       (62, 'nduckiebots', '# Duckiebots', 'Number of duckiebots available', 6),
       (63, 'map_3x3', 'Map 3x3 avaiable', 'The 3x3 loop is available.', 6);

# XXX: the "evaluation steps" are not implemented yet
# TODO: add a "timeout" to each step
CREATE TABLE aido_challenges_evaluation_steps (
  step_id               bigint(20) unsigned unique auto_increment primary key,
  step_name             VARCHAR(128) not null,
  step_description      VARCHAR(1000),
  challenge_id          bigint(20) unsigned references aido_challenges (challenge_id),
  # if this is null then it means execute at the start
  #   triggered_after_step_id       bigint(20) unique,
  #   triggered_after_step_result  ENUM ('evaluating', 'timeout', 'success', 'failed', 'error'), # not sure about evaluating
  evaluation_parameters JSON not null
);

# CREATE TABLE aido_challenges_evaluation_steps_transitions (
#   transition_id bigint(20) unsigned unique auto_increment primary key,
#
#   step_id bigint(20) unsigned not null references aido_challenges_evaluation_steps(step_id),
#   # if this is null, then it means execute at the start of the job
#   previous_step_id bigint(20) unsigned  references aido_challenges_evaluation_steps(step_id),
#   previous_step_result  ENUM ('evaluating', 'timeout', 'success', 'failed', 'error')
# );

create table aido_challenges_evaluation_steps_req_features (
  req_id                bigint(20) unsigned unique auto_increment primary key,
  step_id               bigint(20) unsigned not null  references aido_challenges_evaluation_steps (step_id),
  evaluation_feature_id bigint(20) unsigned not null references aido_evaluation_features (evaluation_feature_id),
  # "minimum amount" necessary
  # can be null
  min_amount            int
);

#
# insert into aido_challenges_evaluation_steps (step_id, challenge_id, step_name, step_description,
#                                               evaluation_parameters) values
#   (11, 1, 'sim-learning', 'Learning step on the cloud',   '{
#     "image": "XXX",
#     "env": "XXX"
#   }'),
#   (12, 1, 'sim-eval-short', 'Short evaluation on the cloud',   '{
#     "image": "XXX",
#     "env": "XXX"
#   }'),
#   (13, 1, 'sim-eval-long', 'Long evaluation on the cloud',    '{
#     "image": "XXX",
#     "env": "XXX"
#   }'),
#   (14, 1, 'real-eval-short', 'Robotarium short ',   '{
#     "image": "XXX",
#     "env": "XXX"
#   }'),
#   (15, 1, 'real-eval-long', 'Robotarium long',   '{
#     "image": "XXX",
#     "env": "XXX"
#   }');
#
# insert into aido_challenges_evaluation_steps_transitions(previous_step_id, previous_step_result, step_id)
# values
#        (null, null, 11),
#        (11, 'success', 12),
#        (12, 'success', 13),
#        (13, 'success', 14),
#        (14, 'success', 15);


# # require at least 300MB of ram
# insert into aido_challenges_evaluation_steps_req_features(step_id, evaluation_feature_id, min_amount)
# values
# # require at least 300MB of ram
# (11, 21, 300),
# # require 50 GB of disk space
# (11, 31, 50000);

create table aido_evaluators (
  evaluator_id      bigint(20) unsigned auto_increment primary key,
  ip4               VARCHAR(120)        not null,
  # these two are provided by the client
  machine_id        VARCHAR(120)        not null, # identification provided by machine
  process_id        VARCHAR(120)        not null, # identification provided by machine
  evaluator_version VARCHAR(120)        not null, # identification provided by machine
  # first contact with this evaluator
  first_heard       datetime            not null,
  last_heard        datetime            not null,
  # The owner of this machine
  # todo: change to "owner_id"
  uid               bigint(20) unsigned not null references wp_users (ID),
  npings            int

  #   unique key `uid_ip4`(`uid`, `ip4`, `machine_id`)
);

# keep track of the features that each evaluator offers
create table aido_evaluators_features (
  aido_evaluators_feature_id bigint(20) unsigned unique auto_increment primary key,

  evaluator_id               bigint(20) unsigned not null references aido_evaluators (evaluator_id),
  evaluation_feature_id      bigint(20) unsigned not null references aido_evaluation_features (evaluation_feature_id),

  # "how much" of the feature (nrobots, etc.)
  amount                     int
);

create table aido_log_categories (
  log_category_id bigint(20) unsigned auto_increment primary key,

  # short tag, which is url compatible (lowercase, a, b, ..., z, '-', '_')
  category_tag    varchar(32) unique  not null,
  category_name   varchar(128) unique not null,

  # Whether the entries should be available to the public, or only to administrators.
  public          bool
);


create table aido_log_entries (
  log_entry_id       bigint(20) unsigned auto_increment primary key,
  log_category_id    bigint(20) unsigned references aido_log_categories (log_category_id),
  timestamp          datetime not null,

  # short version, which should be displayable on one line
  content_short_html varchar(256),

  # long version
  content_long_html  varchar(5020),

  # usual semantics
  log_level          ENUM ('debug', 'info', 'warning', 'error'),

  # category, to be used for filtering

  # we allow one ID for each table - all of these can be null
  #
  # For example, if we have a log event about a job failing,
  # we would have job_id, submission_id, step_id, challenge_id, submitter_id
  #
  # If we have a log like, "new evaluator contacted"
  # then only evaluator_id and evaluator_owner_id would be set.


  evaluator_id       bigint(20) unsigned references aido_evaluators (evaluator_id),
  # person who owns evaluator
  evaluator_owner_id bigint(20) unsigned references wp_users (ID),

  challenge_id       bigint(20) unsigned references aido_challenges (challenge_id),
  step_id            bigint(20) unsigned references aido_challenges_evaluation_steps (step_id),
  job_id             bigint(20) unsigned references aido_evaluation_jobs (job_id),
  submission_id      bigint(20) unsigned references aido_submissions (submission_id),
  submitter_id       bigint(20) unsigned references wp_users (ID),

  # user that made this admin action
  admin_id           bigint(20) unsigned references wp_users (ID)



);

# in the log entries you can use the following macros:
#
#    {admin_id}, {evaluator_id}, challenge_id, step_id, job_id, submission_id, admin_id
#
# plus the following which will evaluate to the hyperlinked name of the entity:
#
#  {admin}  - name of the admin
#  {evaluator}
#  {evaluator_owner}
#  {submitter}
#  {challenge}
#  {step}
#  {job}
#  {submission}
#

insert into aido_log_categories (log_category_id, category_tag, category_name, public)
values
       (1, 'public', 'Public logs', true),
       (2, 'private', 'Private logs', false);


insert into aido_log_entries (log_category_id, timestamp, content_short_html, content_long_html, log_level, admin_id)
values (1, now(), 'Database created by {admin}', 'The database was created.', 'info', 3);







