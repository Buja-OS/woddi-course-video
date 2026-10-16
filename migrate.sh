#!/bin/bash
# Copy WODDI Institute from the restricted Supabase project to a new one. Only counts and error lines are logged.
set -u
LOG=log.txt; : > $LOG
say() { echo "$*" | tee -a $LOG; }
SCH="-n public -n private -n backup -n mp_private"
say "pg_dump $(pg_dump --version)"
case "${MODE:-test}" in check|acl|sql|e2e|shots) DUMP=0;; *) DUMP=1;; esac
if [ "$DUMP" = 1 ]; then
pg_dump "$OLD_URL" --schema-only --no-owner $SCH -f schema.sql 2> e1.txt; say "schema dump exit=$? bytes=$(wc -c < schema.sql) tables=$(grep -c '^CREATE TABLE' schema.sql) functions=$(grep -c '^CREATE FUNCTION\|^CREATE OR REPLACE FUNCTION' schema.sql) policies=$(grep -c '^CREATE POLICY' schema.sql) triggers=$(grep -c '^CREATE TRIGGER' schema.sql)"; sed 's/^/  /' e1.txt | head -20 >> $LOG
pg_dump "$OLD_URL" --data-only --no-owner $SCH -f data_app.sql 2> e2.txt; say "app data dump exit=$? bytes=$(wc -c < data_app.sql)"; sed 's/^/  /' e2.txt | head -20 >> $LOG
pg_dump "$OLD_URL" --data-only --no-owner -t auth.users -t auth.identities -t auth.mfa_factors -t storage.buckets -f data_auth.sql 2> e3.txt; say "auth data dump exit=$? bytes=$(wc -c < data_auth.sql)"; sed 's/^/  /' e3.txt | head -20 >> $LOG
fi
if [ "${MODE:-test}" = "test" ]; then say "test mode: stop before restore"; exit 0; fi
NEW_URL=""
for pw in "$NEW_PW1" "$NEW_PW2"; do for r in eu-west-1 eu-west-2 eu-west-3 eu-central-1 eu-central-2 eu-north-1; do for a in aws-0 aws-1; do
  u="postgresql://postgres.$NEW_REF:$pw@$a-$r.pooler.supabase.com:5432/postgres"
  if PGCONNECT_TIMEOUT=8 psql "$u" -At -c "select 1" >/dev/null 2>e0.txt; then NEW_URL="$u"; say "new project reached at $a-$r with password $( [ "$pw" = "$NEW_PW1" ] && echo 1 || echo 2 )"; break 3; fi
  grep -q "password authentication failed" e0.txt && say "  $a-$r: project found, password $( [ "$pw" = "$NEW_PW1" ] && echo 1 || echo 2 ) wrong"
done; done; done
[ -z "$NEW_URL" ] && { say "could not reach the new project with either password"; exit 1; }

if [ "$MODE" = "shots" ]; then QA_SCRIPT=shots.mjs ./e2e.sh "$NEW_URL" >> $LOG 2>&1; say "done"; exit 0; fi
if [ "$MODE" = "e2e" ]; then ./e2e.sh "$NEW_URL" >> $LOG 2>&1; say "done"; exit 0; fi
if [ "$MODE" = "sql" ]; then for f in apply/*.sql; do psql "$NEW_URL" -v ON_ERROR_STOP=1 -q -f "$f" > a.out 2> a.err; say "applied $f exit=$? errors=$(grep -c ERROR a.err)"; grep -E "ERROR|NOTICE" a.err | head -5 | cut -c1-200 | sed "s/^/    /" >> $LOG; done; [ -f apply/check.sql ] || true; for q in apply/*.q; do [ -f "$q" ] && { say "== $q"; psql "$NEW_URL" -At -F" | " -f "$q" 2>&1 | head -40 | sed "s/^/  /" >> $LOG; }; done; say "done"; exit 0; fi
if [ "$MODE" = "acl" ]; then ./acl.sh "$OLD_URL" "$NEW_URL" >> $LOG 2>&1; say "done"; exit 0; fi
if [ "$MODE" = "check" ]; then ./check.sh "$OLD_URL" "$NEW_URL" >> $LOG 2>&1; say "done"; exit 0; fi
say "== restore"
psql "$NEW_URL" -v ON_ERROR_STOP=1 -q -c "create extension if not exists pg_trgm with schema extensions; create extension if not exists pg_cron; create extension if not exists pg_net with schema extensions; create extension if not exists \"uuid-ossp\" with schema extensions; create extension if not exists pgcrypto with schema extensions;" >> $LOG 2>&1; say "extensions exit=$?"
psql "$NEW_URL" -v ON_ERROR_STOP=0 -q -f schema.sql > s.out 2> s.err; say "schema restore errors=$(grep -c ERROR s.err)"; grep ERROR s.err | sort | uniq -c | sort -rn | head -40 | sed 's/^/  /' >> $LOG
psql "$NEW_URL" -v ON_ERROR_STOP=0 -q -c "SET session_replication_role = replica" -f data_auth.sql -f data_app.sql > d.out 2> d.err; say "data restore errors=$(grep -c ERROR d.err)"; grep ERROR d.err | cut -c1-200 | sort | uniq -c | sort -rn | head -40 | sed 's/^/  /' >> $LOG
psql "$NEW_URL" -v ON_ERROR_STOP=0 -q -f post.sql > p.out 2> p.err; say "post steps errors=$(grep -c ERROR p.err)"; grep ERROR p.err | cut -c1-200 | head -20 | sed 's/^/  /' >> $LOG
say "== row counts old/new"
Q="select n.nspname||'.'||c.relname, c.oid::regclass::text from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname in ('public','private','backup','mp_private') order by 1"
psql "$OLD_URL" -At -F' ' -c "$Q" | while read t r; do o=$(psql "$OLD_URL" -At -c "select count(*) from $r" 2>/dev/null); n=$(psql "$NEW_URL" -At -c "select count(*) from $r" 2>/dev/null); [ "$o" != "$n" ] && echo "  DIFF $t old=$o new=$n" >> $LOG; done
for t in auth.users auth.identities storage.buckets; do o=$(psql "$OLD_URL" -At -c "select count(*) from $t"); n=$(psql "$NEW_URL" -At -c "select count(*) from $t"); say "  $t old=$o new=$n"; done
say "done"
