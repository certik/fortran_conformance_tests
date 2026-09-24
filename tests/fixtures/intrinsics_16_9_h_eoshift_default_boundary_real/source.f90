! rule: S16.9.77-004
! covers: EOSHIFT-default-boundary-real-zero
program i169h_eoshift_default_boundary_real
  implicit none
  real :: a(3), r(3), q(3)
  integer :: checks
  checks = 0
  a = [4.0, 5.0, 6.0]
  r = eoshift(a, 1); q = eoshift(a, 1, 9.0)
  call require('EOSHIFT-default-boundary-real-zero', &
       r(3) == 0.0 .and. q(3) == 9.0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT DEFAULT BOUNDARY REAL OK'
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
end program i169h_eoshift_default_boundary_real
