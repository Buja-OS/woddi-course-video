select 'saves since move: user_progress', count(*) from public.user_progress where updated_at > '2026-10-16 03:30+00';
select 'saves since move: course_progress', count(*) from public.course_progress where updated_at > '2026-10-16 03:30+00';
select 'sign-ins since move', count(*) from auth.users where last_sign_in_at > '2026-10-16 03:30+00';
select 'new accounts since move', count(*) from auth.users where created_at > '2026-10-16 03:30+00';
select 'test account progress', up.rooting_started, coalesce(array_length(up.rooting_modules_done,1),0), up.blueprint_pillars_done::text, up.updated_at from public.users u left join public.user_progress up on up.uid=u.uid where md5(lower(u.email))='4cc5a5814a4a2fae49e5f390d93a4e80';
select 'test account course modules', count(distinct module_id) from public.course_progress p join public.users u on u.uid=p.uid where md5(lower(u.email))='4cc5a5814a4a2fae49e5f390d93a4e80' and p.completed;
select 'progress rows with errors-style empty uid', count(*) from public.user_progress where uid is null or uid='';
