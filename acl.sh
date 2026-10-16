#!/bin/bash
# Make the new project's permissions for anon / authenticated / service_role / PUBLIC exactly match the old project.
export LC_ALL=C
O="$1"; N="$2"
psql "$O" -At -q -f acl_list.sql | sort > acl_old.txt; psql "$N" -At -q -f acl_list.sql | sort > acl_new.txt
echo "  permission entries old=$(wc -l < acl_old.txt) new=$(wc -l < acl_new.txt) differing=$(comm -3 acl_old.txt acl_new.txt | wc -l)"
comm -3 acl_old.txt acl_new.txt | sed "s/^\t//" | awk -F'|' '{print $1}' | sort | uniq -c | sed 's/^/    by kind: /'
# objects that differ -> revoke everything for the 4 grantees, then grant exactly what the old project had
comm -3 acl_old.txt acl_new.txt | sed 's/^\t//' | awk -F'|' '{print $1"|"$2}' | sort -u > touch.txt
python3 - <<'PY' > fix.sql
import collections
old=collections.defaultdict(list)
for l in open('acl_old.txt'):
    k,nm,g,p=l.rstrip('\n').split('|')
    if k!='column': old[(k,nm)].append((g,p))
cols=collections.defaultdict(list)
for l in open('acl_old.txt'):
    if l.startswith('column|'):
        _,nm,g,p=l.rstrip('\n').split('|'); cols[nm].append((g,p))
out=['begin;','set search_path = \'\';']
kw={'function':'function','table':'table','sequence':'sequence','schema':'schema'}
for l in open('touch.txt'):
    k,nm=l.rstrip('\n').split('|',1)
    if k=='column':
        t,c=nm.rsplit('.',1)  # column names here are simple identifiers
        out.append(f"revoke all ({c}) on table {t} from public, anon, authenticated, service_role;")
        for g,p in cols.get(nm,[]): out.append(f"grant {p} ({c}) on table {t} to {g};")
        continue
    out.append(f"revoke all on {kw[k]} {nm} from public, anon, authenticated, service_role;")
    for g,p in old.get((k,nm),[]): out.append(f"grant {p} on {kw[k]} {nm} to {g};")
out.append('commit;')
print('\n'.join(out))
PY
echo "  fix statements: $(grep -c '^grant\|^revoke' fix.sql)"
psql "$N" -v ON_ERROR_STOP=1 -q -f fix.sql > f.out 2> f.err; echo "  apply exit=$? errors=$(grep -c ERROR f.err)"; grep ERROR f.err | head -5 | cut -c1-200 | sed 's/^/    /'
psql "$N" -At -q -f acl_list.sql | sort > acl_new2.txt
echo "  after fix differing=$(comm -3 acl_old.txt acl_new2.txt | wc -l)"; comm -3 acl_old.txt acl_new2.txt | head -8 | cut -c1-160 | sed 's/^/    /'
# realtime: add tables the old project published that the new one does not
psql "$O" -At -c "select quote_ident(schemaname)||'.'||quote_ident(tablename) from pg_publication_tables where pubname='supabase_realtime' order by 1" | sort > rt_old.txt
psql "$N" -At -c "select quote_ident(schemaname)||'.'||quote_ident(tablename) from pg_publication_tables where pubname='supabase_realtime' order by 1" | sort > rt_new.txt
for t in $(comm -23 rt_old.txt rt_new.txt); do psql "$N" -q -c "alter publication supabase_realtime add table $t" 2>&1 | grep ERROR | sed 's/^/    /'; done
echo "  realtime tables now old=$(wc -l < rt_old.txt) new=$(psql "$N" -At -c "select count(*) from pg_publication_tables where pubname='supabase_realtime'")"
