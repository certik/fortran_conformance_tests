! rule: S19.1-002
! covers: local-identifier-inclusive-scope nested-scope-shadowing-exclusion
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_rename_provider
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_rename_provider
program scoping_host_rename_shadow
  use scoping_rename_provider, only: local_name => source_name, wrong_global
  implicit none
  integer :: token, source_name, host_seen, inner_seen, checks
  token = 41
  source_name = 99
  host_seen = -11
  inner_seen = -12
  checks = 0
  call read_host_token()
  call read_shadow_token()
  call expect_equal(host_seen, 41, 'host association same identifier')
  call expect_equal(inner_seen, 73, 'nested local identifier')
  call expect_equal(token, 41, 'host token unchanged')
  call expect_equal(local_name, 52, 'use rename associated value')
  call expect_equal(source_name, 99, 'local use-name homonym unchanged')
  call expect_equal(checks, 5, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 HOST RENAME SHADOW OK'
contains
  subroutine read_host_token()
    implicit none
    host_seen = token
  end subroutine read_host_token
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
end program scoping_host_rename_shadow
