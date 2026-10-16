select cohort, count(*) from public.certificates group by 1 order by 2 desc;
select (public.verify_credential((select credential_code from public.certificates where credential_code is not null limit 1)))->>'cohort';
select count(*) from public.certificates where cohort is null;
