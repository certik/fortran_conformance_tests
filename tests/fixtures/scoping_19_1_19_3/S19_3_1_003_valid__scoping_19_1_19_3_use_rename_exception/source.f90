! rule: S19.3.1-003
! covers: use-rename-use-name-exception
! evidence: effect
! standard: f2023
! oracle-basis: standard
module scoping_use_rename_exception_mod
  implicit none
  integer :: source_name = 52
  integer :: wrong_global = 77
end module scoping_use_rename_exception_mod
program scoping_use_rename_exception
  use scoping_use_rename_exception_mod, only: local_name => source_name, wrong_global
  implicit none
  integer :: source_name, checks
  source_name = 99
  checks = 0
  call expect_equal(local_name, 52, 'use-name in rename')
  call expect_equal(source_name, 99, 'local homonym for use-name')
  call expect_equal(checks, 2, 'check count before completion')
  write(*,'(a)') 'SCOPING 19.1-19.3 USE RENAME EXCEPTION OK'
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
end program scoping_use_rename_exception
