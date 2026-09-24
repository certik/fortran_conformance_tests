! rule: S19.1-004
! covers: same-identifier-different-scope-association different-identifier-different-scope-association
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_association_rename_mod
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_association_rename_mod
program scoping_association_rename
  use scoping_association_rename_mod, only: local_name => source_name, wrong_global
  implicit none
  integer :: token, source_name, host_seen, checks
  token = 41
  source_name = 99
  host_seen = -11
  checks = 0
  call read_host_token()
  call expect_equal(host_seen, 41, 'same identifier host association')
  call expect_equal(local_name, 52, 'different identifier use rename')
  call expect_equal(source_name, 99, 'local use-name sentinel')
  call expect_equal(token, 41, 'host token unchanged')
  call expect_equal(checks, 4, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 ASSOCIATION RENAME OK'
contains
  subroutine read_host_token()
    implicit none
    host_seen = token
  end subroutine read_host_token
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
end program scoping_association_rename
