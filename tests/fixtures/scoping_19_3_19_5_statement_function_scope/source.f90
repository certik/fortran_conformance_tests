! rule: S19.4-014
! covers: statement-function-dummy-statement-scope
! covers: statement-function-dummy-scalar-type-from-enclosing
program scoping_19_3_19_5_statement_function_scope
  implicit integer (r)
  integer :: checks
  integer :: q, sf, sg, observed, implicit_observed
  sf(q) = q + 1
  sg(r) = r + 2
  checks = 0
  q = 99
  observed = sf(4)
  implicit_observed = sg(5)
  if (observed /= 5) then
    write(*,'(a)') 'SCOPE:statement_function_scope:dummy-scope'
    error stop
  end if
  checks = checks + 1
  if (q /= 99) then
    write(*,'(a)') 'SCOPE:statement_function_scope:outer'
    error stop
  end if
  checks = checks + 1
  if (implicit_observed /= 7) then
    write(*,'(a)') 'SCOPE:statement_function_scope:implicit-type'
    error stop
  end if
  checks = checks + 1
  if (checks /= 3) then
    write(*,'(a)') 'SCOPE:statement_function_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 STATEMENT FUNCTION SCOPE OK'
contains
end program scoping_19_3_19_5_statement_function_scope
