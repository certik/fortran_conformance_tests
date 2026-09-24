! rule: S19.4-002
! covers: statement-entity-common-block-name-exception
! covers: statement-entity-scalar-variable-name-exception
module scoping_common_holder
  implicit none
  integer :: common_payload
  common /idx/ common_payload
end module

program scoping_19_3_19_5_statement_entity_exceptions
  use scoping_common_holder, only: common_payload
  implicit integer (i)
  integer :: checks
  integer :: i, idx_values(3), scalar_values(3)
  checks = 0
  i = 99
  common_payload = -505
  data (idx_values(idx), idx = 1, 3) / 101, 102, 103 /
  scalar_values = [(i, i = 1, 3)]
  if (any(idx_values /= [101, 102, 103])) then
    write(*,'(a)') 'SCOPE:statement_entity_exceptions:common-name-data'
    error stop
  end if
  checks = checks + 1
  if (common_payload /= -505) then
    write(*,'(a)') 'SCOPE:statement_entity_exceptions:common-storage-sentinel'
    error stop
  end if
  checks = checks + 1
  if (any(scalar_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:statement_entity_exceptions:scalar-exception-values'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:statement_entity_exceptions:scalar-exception-outer'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:statement_entity_exceptions:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 STATEMENT ENTITY EXCEPTIONS OK'
contains
end program scoping_19_3_19_5_statement_entity_exceptions
