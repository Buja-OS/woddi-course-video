select 'anon policies on users', count(*) from pg_policies where tablename='users' and policyname='anyone can read public profiles';
select 'admin_user_growth definer', prosecdef from pg_proc where oid='public.admin_user_growth()'::regprocedure;
select 'phone_registered exists', count(*) from pg_proc where proname='phone_registered';
