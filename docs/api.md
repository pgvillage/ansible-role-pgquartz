# pgvillage.pgquartz API

This document describes all variables of the `pgvillage.pgquartz` role.
Defaults are defined in [defaults/main.yml](../defaults/main.yml).

## Overview

| Variable | Default | Description |
| --- | --- | --- |
| `pgquartz_cron_mailto` | `{{ pgquartz_osuser }}@{{ inventory_hostname }}` | Address cron mails job output to |
| `pgquartz_configdir` | `/etc/pgquartz` | pgquartz configuration directory |
| `pgquartz_jobsdir` | `{{ pgquartz_configdir }}/jobs` | Job definitions directory |
| `pgquartz_osuser` | `pgquartz` | OS user owning files and running jobs |
| `pgquartz_osgroup` | `pgquartz` | OS group of `pgquartz_osuser` |
| `pgquartz_uid` | `9745` | UID of `pgquartz_osuser` |
| `pgquartz_gid` | `9745` | GID of `pgquartz_osgroup` |
| `pgquartz_package_state` | `present` | State of packages, OS user and OS group |
| `pgquartz_packages` | `[pgquartz, git]` | Packages to install from repositories |
| `pgquartz_local_packages` | `[]` | Local package files to copy and install |
| `pgquartz_definitions` | `[]` | Git repositories with job definitions |
| `pgquartz_jobs` | `[]` | Jobs to schedule |
| `pgquartz_cert_managed` | `true` | Deploy client certificates to `~/.postgresql/` |
| `pgquartz_ca_chain` | `--- CA ---` | CA chain (`root.crt`) |
| `pgquartz_cert` | `--- CERT ---` | Client certificate (`postgresql.crt`) |
| `pgquartz_cert_key` | `--- KEY ---` | Client private key (`postgresql.key`) |
| `pgquartz_logfolder` | `/var/log/pgquartz` | Log directory |
| `pgquartz_scheduler` | `systemd` | Scheduler implementation |
| `pgquartz_cronvars` | `MAILTO`, `LOGFILE` | Variables in `/etc/cron.d/pgquartz` |
| `pgquartz_logrotate_config` | daily, keep 7 | Content of `/etc/logrotate.d/pgquartz` |

## Directories

### `pgquartz_configdir`

Directory holding the pgquartz configuration. Created with owner `pgquartz_osuser`,
group `pgquartz_osgroup` and mode `0755`.

Default: `/etc/pgquartz`

### `pgquartz_jobsdir`

Directory holding the pgquartz job definitions. Created like `pgquartz_configdir`.
With the cron scheduler, job `<name>` runs `{{ pgquartz_jobsdir }}/<name>.yml`.

Default: `{{ pgquartz_configdir }}/jobs`

### `pgquartz_logfolder`

Directory for pgquartz log files. With the cron scheduler it is created (mode `0700`),
passed as the `LOGFILE` cronvar and used by `pgquartz_logrotate_config`.
With the timer scheduler it is removed.

Default: `/var/log/pgquartz`

## OS user and group

### `pgquartz_osuser`

OS user that owns the pgquartz files and runs the jobs. Created as a system user with a home directory.

Default: `pgquartz`

### `pgquartz_osgroup`

OS group of `pgquartz_osuser`. Created as a system group.

Default: `pgquartz`

### `pgquartz_uid`

UID for `pgquartz_osuser`.

Default: `9745`

### `pgquartz_gid`

GID for `pgquartz_osgroup`.

Default: `9745`

## Installation

### `pgquartz_package_state`

State of the pgquartz packages, OS user and OS group (`present`, `absent`, `latest`, ...).

Default: `present`

### `pgquartz_packages`

Packages to install from the configured package repositories.

Default:

```yaml
pgquartz_packages:
  - pgquartz
  - git
```

### `pgquartz_local_packages`

Local package files (resolved from the role / playbook files path) that are copied to `/tmp`
and installed from there. Useful when pgquartz is not available from a repository.

Default: `[]`

Example:

```yaml
pgquartz_local_packages:
  - pgquartz-1.0.0-1.x86_64.rpm
```

## Certificates

### `pgquartz_cert_managed`

When `true`, the certificates below are deployed to `~/.postgresql/` of `pgquartz_osuser`
so that pgquartz can connect to PostgreSQL with client certificate authentication.

Default: `true`

### `pgquartz_ca_chain`

CA chain (PEM) deployed as `~/.postgresql/root.crt` (mode `0640`).

Default: `--- CA ---` (placeholder)

### `pgquartz_cert`

Client certificate (PEM) deployed as `~/.postgresql/postgresql.crt` (mode `0640`).

Default: `--- CERT ---` (placeholder)

### `pgquartz_cert_key`

Client private key (PEM) deployed as `~/.postgresql/postgresql.key` (mode `0600`).
Store this in Ansible Vault.

Default: `--- KEY ---` (placeholder)

## Scheduling

### `pgquartz_scheduler`

Scheduler used to run the jobs. The role includes `tasks/jobs_<pgquartz_scheduler>.yml`.
Available implementations:

| Value | Behaviour |
| --- | --- |
| `cron` | Checks out `pgquartz_definitions`, schedules `pgquartz_jobs` in `/etc/cron.d/pgquartz`, sets `pgquartz_cronvars` and deploys `pgquartz_logrotate_config` |
| `timer` | Deploys systemd `pgquartz.service` / `pgquartz.timer` units and removes the cron file and log folder |
| `external` | Nothing is scheduled; scheduling is left to an external tool |

Default: `systemd`

### `pgquartz_definitions`

Git repositories with job definitions to check out (only used with the `cron` scheduler).

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `url` | yes | | Git repository to clone |
| `dest` | yes | | Directory to clone into |
| `branch` | no | `master` | Branch / tag / commit to check out |

Default: `[]`

Example:

```yaml
pgquartz_definitions:
  - url: https://[user]:[apikey]@github.com/mannemsolutions/pgquartz_jobs.git
    dest: "{{ pgquartz_jobsdir }}/jobs/"
    branch: dev
```

### `pgquartz_jobs`

Jobs to schedule (only used with the `cron` scheduler). Each job runs
`pgquartz -c '{{ pgquartz_jobsdir }}/<name>.yml'` as `pgquartz_osuser`.

| Key | Required | Default | Description |
| --- | --- | --- | --- |
| `name` | yes | | Job name, also the name of the job definition file |
| `minute` | no | `*` | Cron minute |
| `hour` | no | `*` | Cron hour |
| `dom` | no | `*` | Cron day of month |
| `month` | no | `*` | Cron month |
| `dow` | no | `*` | Cron day of week |

Default: `[]`

Example (runs `/etc/pgquartz/jobs/myjob.yml` every day at 01:30):

```yaml
pgquartz_jobs:
  - name: myjob
    minute: "30"
    hour: "1"
```

### `pgquartz_cron_mailto`

Address cron mails job output to. Used for the `MAILTO` entry in `pgquartz_cronvars`.

Default: `{{ pgquartz_osuser }}@{{ inventory_hostname }}`

### `pgquartz_cronvars`

Variables set in `/etc/cron.d/pgquartz` (only used with the `cron` scheduler).
Each item has a `name` and a `value`.

Default:

```yaml
pgquartz_cronvars:
  - name: MAILTO
    value: "{{ pgquartz_cron_mailto }}"
  - name: LOGFILE
    value: "{{ pgquartz_logfolder }}"
```

### `pgquartz_logrotate_config`

Content of `/etc/logrotate.d/pgquartz` (only used with the `cron` scheduler).

Default:

```
{{ pgquartz_logfolder }}/*.log {
    daily
    rotate 7
    copytruncate
    delaycompress
    compress
    notifempty
    missingok
    su root root
}
```
