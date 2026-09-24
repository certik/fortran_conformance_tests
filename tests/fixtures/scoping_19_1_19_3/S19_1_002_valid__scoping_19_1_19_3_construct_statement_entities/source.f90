! rule: S19.1-002
! covers: construct-identifier-construct-scope statement-identifier-statement-scope
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_construct_statement_entities
  implicit none
  integer :: i, checks
  integer :: concurrent_values(3), implied_values(3), construct_source(3), wrong_source(3)
  i = 99
  checks = 0
  concurrent_values = -7
  construct_source = [1, 2, 3]
  wrong_source = [7, 8, 9]
  associate (i => construct_source)
    concurrent_values = i * 10
  end associate
  implied_values = [(i, i = 1, 3)]
  call expect_equal(concurrent_values(1), 10, 'do concurrent first')
  call expect_equal(concurrent_values(2), 20, 'do concurrent second')
  call expect_equal(concurrent_values(3), 30, 'do concurrent third')
  call expect_equal(implied_values(1), 1, 'implied do first')
  call expect_equal(implied_values(2), 2, 'implied do second')
  call expect_equal(implied_values(3), 3, 'implied do third')
  call expect_equal(i, 99, 'outer i sentinel')
  call expect_equal(checks, 7, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 CONSTRUCT STATEMENT ENTITIES OK'
contains
  subroutine expect_equal(observed, expected, label)
    implicit none
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'SCOPE-CHECK-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine expect_equal
end program scoping_construct_statement_entities
