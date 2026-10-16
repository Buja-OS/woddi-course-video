set search_path = '';
with objs as (
  select 'function' k, p.oid::regprocedure::text nm, coalesce(p.proacl, acldefault('f', p.proowner)) acl, p.oid
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname in ('public','private','backup','mp_private') and not exists (select 1 from pg_depend d where d.objid=p.oid and d.deptype='e')
  union all
  select case c.relkind when 'S' then 'sequence' else 'table' end, c.oid::regclass::text, coalesce(c.relacl, acldefault((case c.relkind when 'S' then 's' else 'r' end)::"char", c.relowner)), c.oid
    from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname in ('public','private','backup','mp_private') and c.relkind in ('r','v','m','S','p','f') and not exists (select 1 from pg_depend d where d.objid=c.oid and d.deptype='e')
  union all
  select 'schema', quote_ident(n.nspname), coalesce(n.nspacl, acldefault('n', n.nspowner)), n.oid from pg_namespace n where n.nspname in ('public','private','backup','mp_private')
)
select o.k||'|'||o.nm||'|'||case when a.grantee=0 then 'public' else r.rolname end||'|'||a.privilege_type
  from objs o cross join lateral aclexplode(o.acl) a left join pg_roles r on r.oid=a.grantee
 where a.grantee=0 or r.rolname in ('anon','authenticated','service_role')
union all
select 'column|'||c.oid::regclass::text||'.'||quote_ident(at.attname)||'|'||case when a.grantee=0 then 'public' else r.rolname end||'|'||a.privilege_type
  from pg_attribute at join pg_class c on c.oid=at.attrelid join pg_namespace n on n.oid=c.relnamespace
  cross join lateral aclexplode(at.attacl) a left join pg_roles r on r.oid=a.grantee
 where n.nspname in ('public','private','backup','mp_private') and at.attacl is not null and (a.grantee=0 or r.rolname in ('anon','authenticated','service_role'))
order by 1;
