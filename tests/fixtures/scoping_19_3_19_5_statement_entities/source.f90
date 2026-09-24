! rule: S19.4-001
! covers: statement-entity-class-list
! covers: statement-entity-shadows-outer-identifier
program scoping_19_3_19_5_statement_entities
  implicit none
  integer :: checks
  integer :: i, di, k, q, sf
  integer :: ac_values(3), data_values(3), forall_values(3)
  sf(q) = q + 1
  checks = 0
  i = 99
  di = 88
  k = 77
  q = 66
  ac_values = -1
  forall_values = -2
  data (data_values(di), di = 1, 3) / 10, 20, 30 /
  ac_values = [(i, i = 1, 3)]
  forall (k = 1:3) forall_values(k) = k + 40
  if (any(ac_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:statement_entities:array-constructor-values'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:statement_entities:array-constructor-outer'
    error stop
  end if
  checks = checks + 1
  if (any(data_values /= [10, 20, 30])) then
    write(*,'(a)') 'SCOPE:statement_entities:data-values'
    error stop
  end if
  checks = checks + 1
  if (di /= 88) then
    write(*,'(a)') 'SCOPE:statement_entities:data-outer'
    error stop
  end if
  checks = checks + 1
  if (any(forall_values /= [41, 42, 43])) then
    write(*,'(a)') 'SCOPE:statement_entities:forall-statement-values'
    error stop
  end if
  checks = checks + 1
  if (k /= 77) then
    write(*,'(a)') 'SCOPE:statement_entities:forall-statement-outer'
    error stop
  end if
  checks = checks + 1
  if (sf(4) /= 5) then
    write(*,'(a)') 'SCOPE:statement_entities:statement-function-value'
    error stop
  end if
  checks = checks + 1
  if (q /= 66) then
    write(*,'(a)') 'SCOPE:statement_entities:statement-function-outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 8) then
    write(*,'(a)') 'SCOPE:statement_entities:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 STATEMENT ENTITIES OK'
contains
end program scoping_19_3_19_5_statement_entities
