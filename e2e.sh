#!/bin/bash
# Live check of woddiinstitute.com with two temporary accounts (one admin, one learner) that are deleted at the end.
# Public log: counts only. Details and screenshots are encrypted for the WODDI engineer (qa.pub) before they leave the runner.
N="$1"; RID="${GITHUB_RUN_ID:-local}"
AE="qa-admin-$RID@woddiinstitute.com"; SE="qa-learner-$RID@woddiinstitute.com"
AP=$(openssl rand -hex 16); SP=$(openssl rand -hex 16)
mk() { psql "$N" -At -q -v ON_ERROR_STOP=1 2>/dev/null <<SQL
with u as (
  insert into auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
    created_at, updated_at, confirmation_token, recovery_token, email_change_token_new, email_change, email_change_token_current, phone_change, phone_change_token, reauthentication_token)
  values ('00000000-0000-0000-0000-000000000000', gen_random_uuid(), 'authenticated', 'authenticated', '$1', extensions.crypt('$2', extensions.gen_salt('bf')), now(),
    '{"provider":"email","providers":["email"]}', '{"name":"$3"}', now(), now(), '', '', '', '', '', '', '', '')
  returning id, email)
insert into auth.identities (id, user_id, provider_id, provider, identity_data, last_sign_in_at, created_at, updated_at)
select gen_random_uuid(), id, id::text, 'email', jsonb_build_object('sub', id::text, 'email', email, 'email_verified', true), now(), now(), now() from u
returning user_id;
SQL
}
cleanup() {
  psql "$N" -q -v ON_ERROR_STOP=0 <<SQL > clean.out 2>&1
do \$\$ declare ids text[]; r record; n int := 0; begin
  select array_agg(id::text) into ids from auth.users where email in ('$AE', '$SE');
  if ids is null then return; end if;
  for r in select table_name, column_name from information_schema.columns c join information_schema.tables t using (table_schema, table_name)
           where c.table_schema = 'public' and t.table_type = 'BASE TABLE' and c.column_name in ('uid', 'user_id') and c.table_name <> 'users' loop
    begin execute format('delete from public.%I where %I::text = any(\$1)', r.table_name, r.column_name) using ids; exception when others then n := n + 1; end;
  end loop;
  delete from public.users where uid = any(ids);
  delete from auth.users where id::text = any(ids);
  raise notice 'qa cleanup done, % tables skipped', n;
end \$\$;
SQL
  echo "  cleanup: $(grep -c 'qa cleanup done' clean.out) done, leftover accounts: $(psql "$N" -At -c "select count(*) from auth.users where email in ('$AE','$SE')")"
}
trap cleanup EXIT
AID=$(mk "$AE" "$AP" "WODDI QA Admin") || { echo "  could not create admin test account"; exit 1; }
SID=$(mk "$SE" "$SP" "Amina QA") || { echo "  could not create learner test account"; exit 1; }
psql "$N" -q -c "update public.users set role='admin', account_type='staff' where uid='$AID'" 2>&1 | grep -i error
echo "  test accounts created (admin + learner)"
CODE=$(psql "$N" -At -c "select credential_code from public.certificates where credential_code is not null and not coalesce(revoked,false) order by issued_at desc limit 1")
npm i --silent --no-audit --no-fund playwright@1.47.2 >/dev/null 2>&1 && npx -y playwright@1.47.2 install --with-deps chromium >/dev/null 2>&1
ADMIN_EMAIL="$AE" ADMIN_PW="$AP" STU_EMAIL="$SE" STU_PW="$SP" CERT="$CODE" timeout 1200 node qa.mjs
echo "  qa script exit=$?"
[ -f qa-summary.txt ] && sed 's/^/  /' qa-summary.txt
mkdir -p enc && tar czf qa.tgz qa-out 2>/dev/null && openssl rand -hex 32 > k.txt && \
  openssl enc -aes-256-cbc -pbkdf2 -salt -in qa.tgz -out enc/qa.tgz.enc -pass file:k.txt && \
  openssl pkeyutl -encrypt -pubin -inkey qa.pub -pkeyopt rsa_padding_mode:oaep -in k.txt -out enc/k.enc && rm -f k.txt qa.tgz && echo "  encrypted results: $(du -sh enc | cut -f1)"
