! rule: S16.9.74-002
! covers: DPROD-result-double-precision-real
program i169h_dprod_result_characteristics
  implicit none
  integer :: checks
  real :: x, y
  checks = 0
  x = 3.0; y = 2.0
  call require('DPROD result is double precision real', kind(dprod(x, y)) == kind(0.0d0), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DPROD RESULT CHARACTERISTICS OK'
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
end program i169h_dprod_result_characteristics
