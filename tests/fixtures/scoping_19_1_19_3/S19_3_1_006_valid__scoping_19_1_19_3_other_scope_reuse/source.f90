! rule: S19.3.1-006
! covers: local-identifier-reuse-in-another-scope
! evidence: effect
! standard: f2023
! oracle-basis: standard
program scoping_other_scope_reuse
  implicit none
  integer :: token, inner_seen, checks
  token = 41
  inner_seen = -12
  checks = 0
  call read_shadow_token()
  call expect_equal(inner_seen, 73, 'reused local identifier')
  call expect_equal(token, 41, 'outer token unchanged')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 OTHER SCOPE REUSE OK'
contains
  subroutine read_shadow_token()
    implicit none
    integer :: token
    token = 73
    inner_seen = token
  end subroutine read_shadow_token
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
end program scoping_other_scope_reuse
