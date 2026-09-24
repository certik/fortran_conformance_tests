! rule: S15.2.2.5-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
program statement_function
  implicit none
  integer :: f, i, result
  f(i) = i + 1
  result = -10
  result = f(41)
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.5 STATEMENT FUNCTION OK'
end program
