#!/bin/bash
# Compare the old and new WODDI databases and test the new project's public API with the public anon key.
O="$1"; N="$2"
q() { psql "$1" -At -F' ' -c "$2" 2>&1 | head -40; }
for L in "policies in public|select count(*) from pg_policies where schemaname='public'" \
         "storage policies|select count(*) from pg_policies where schemaname='storage'" \
         "functions|select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname in ('public','private','backup','mp_private')" \
         "triggers|select count(*) from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace where not t.tgisinternal and n.nspname in ('public','private','backup','mp_private','auth','storage')" \
         "anon can read tables|select count(*) from pg_tables where schemaname='public' and has_table_privilege('anon', quote_ident(schemaname)||'.'||quote_ident(tablename), 'SELECT')" \
         "authenticated can write tables|select count(*) from pg_tables where schemaname='public' and has_table_privilege('authenticated', quote_ident(schemaname)||'.'||quote_ident(tablename), 'INSERT')" \
         "anon can run functions|select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and has_function_privilege('anon', p.oid, 'EXECUTE')" \
         "authenticated can run functions|select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and has_function_privilege('authenticated', p.oid, 'EXECUTE')" \
         "realtime tables|select count(*) from pg_publication_tables where pubname='supabase_realtime'" \
         "cron jobs|select count(*) from cron.job" ; do
  k="${L%%|*}"; sql="${L#*|}"; echo "  $k: old=$(q "$O" "$sql") new=$(q "$N" "$sql")"
done
echo "  tables anon can read on old but not new:"; 
psql "$O" -At -c "select tablename from pg_tables where schemaname='public' and has_table_privilege('anon','public.'||quote_ident(tablename),'SELECT') order by 1" > a.txt
psql "$N" -At -c "select tablename from pg_tables where schemaname='public' and has_table_privilege('anon','public.'||quote_ident(tablename),'SELECT') order by 1" > b.txt
comm -23 a.txt b.txt | head -20 | sed 's/^/    /'
psql "$O" -At -c "select p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and has_function_privilege('authenticated',p.oid,'EXECUTE') order by 1" > c.txt
psql "$N" -At -c "select p.proname from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and has_function_privilege('authenticated',p.oid,'EXECUTE') order by 1" > d.txt
echo "  functions signed-in users could run before but not now: $(comm -23 c.txt d.txt | wc -l)"; comm -23 c.txt d.txt | head -10 | sed 's/^/    /'
echo "  functions open now but closed before: $(comm -13 c.txt d.txt | wc -l)"
echo "  sequences: $(psql "$N" -At -c "select count(*) from pg_sequences where schemaname='public' and coalesce(last_value,0)=0")/$(psql "$N" -At -c "select count(*) from pg_sequences where schemaname='public'") public sequences unset on new"
A='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNtd2h4ZmFza3hzdHR2anZjaWp2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIxMDQwNjQsImV4cCI6MjEwNzY4MDA2NH0.A2kjgE-UnmX8ebzM2qqSXSCZHtmgN4BsiBTMGKVtzBw'
B=https://cmwhxfaskxsttvjvcijv.supabase.co
echo "== public API with the anon key"
echo "  auth health: $(curl -s -o /dev/null -w '%{http_code}' -H "apikey: $A" $B/auth/v1/health)"
echo "  auth settings: $(curl -s -H "apikey: $A" $B/auth/v1/settings | python3 -c 'import sys,json;j=json.load(sys.stdin);print("google",j["external"].get("google"),"email",j["external"].get("email"),"phone",j["external"].get("phone"),"autoconfirm",j.get("mailer_autoconfirm"),"signup_disabled",j.get("disable_signup"))')"
for t in courses course_modules certificates platform_settings; do echo "  rest $t: $(curl -s -o /dev/null -w '%{http_code}' -H "apikey: $A" -H "Authorization: Bearer $A" "$B/rest/v1/$t?select=*&limit=1")"; done
echo "  rpc verify_credential: $(curl -s -o /dev/null -w '%{http_code}' -X POST -H "apikey: $A" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"p_code":"WIA-TEST"}' "$B/rest/v1/rpc/verify_credential")"
echo "  storage public bucket: $(curl -s -o /dev/null -w '%{http_code}' "$B/storage/v1/object/public/course-i18n/fr/_catalog.json")"
echo "  login with wrong password (expect 400 invalid credentials): $(curl -s -X POST -H "apikey: $A" -H 'Content-Type: application/json' -d '{"email":"nobody@example.com","password":"definitely-wrong-123"}' "$B/auth/v1/token?grant_type=password" | head -c 120)"
