! rule: S16.9.77-004
! covers: EOSHIFT-default-boundary-complex-zero
program i169h_eoshift_default_boundary_complex
  implicit none
  complex :: a(3), r(3), q(3)
  integer :: checks
  checks = 0
  a = [cmplx(1.0,1.0), cmplx(2.0,2.0), cmplx(3.0,3.0)]
  r = eoshift(a, 1); q = eoshift(a, 1, (9.0, 1.0))
  call require('EOSHIFT-default-boundary-complex-zero', &
       r(3) == (0.0, 0.0) .and. q(3) == (9.0, 1.0), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT DEFAULT BOUNDARY COMPLEX OK'
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
end program i169h_eoshift_default_boundary_complex
