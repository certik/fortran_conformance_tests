! rule: R1412
! covers: only-generic-spec-form only-use-name-form only-rename-form
! evidence: effect
! standard: f2023
! oracle-basis: standard
module r1412_provider
  implicit none
  integer :: answer = 42
  integer :: wrong = -999
  interface g
    module procedure gi
  end interface
contains
  integer function gi(i)
    integer, intent(in) :: i
    gi = 31 + i - i
  end function
end module
program only_forms
  implicit none
  integer :: checks
  checks = 0
  call check_generic(checks)
  call check_use_name(checks)
  call check_rename(checks)
  if (checks /= 3) error stop 4
  write(*,'(a)') 'USE ASSOCIATION 14.2.2 ONLY FORMS OK'
contains
  subroutine check_generic(checks)
    use r1412_provider, only: g
    implicit none
    integer, intent(inout) :: checks
    if (g(3) /= 31) error stop 1
    checks = checks + 1
  end subroutine
  subroutine check_use_name(checks)
    use r1412_provider, only: answer
    implicit none
    integer, intent(inout) :: checks
    if (answer /= 42) error stop 2
    checks = checks + 1
  end subroutine
  subroutine check_rename(checks)
    use r1412_provider, only: local_answer => answer
    implicit none
    integer, intent(inout) :: checks
    if (local_answer /= 42) error stop 3
    checks = checks + 1
  end subroutine
end program
