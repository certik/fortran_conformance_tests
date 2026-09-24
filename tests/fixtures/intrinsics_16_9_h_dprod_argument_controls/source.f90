! rule: S16.9.74-001
! covers: DPROD-X-default-real
! covers: DPROD-Y-default-real
program i169h_dprod_argument_controls
  implicit none
  integer :: checks
  real :: x, y
  checks = 0
  x = -3.0; y = 2.0
  call require('DPROD X default real positive control', dprod(x, y) == -6.0d0, checks)
  call require('DPROD Y default real positive control', dprod(2.0, y) == 4.0d0, checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DPROD ARGUMENT CONTROLS OK'
contains
  subroutine require(label, condition, checks)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    integer, intent(inout) :: checks
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
    checks = checks + 1
  end subroutine require
end program i169h_dprod_argument_controls
