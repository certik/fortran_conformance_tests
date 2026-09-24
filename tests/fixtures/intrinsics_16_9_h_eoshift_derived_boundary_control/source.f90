! rule: S16.9.77-001
! covers: EOSHIFT-ARRAY-array-any-type
program i169h_eoshift_derived_boundary_control
  implicit none
  type :: payload
    integer :: tag
  end type payload
  integer :: checks
  type(payload) :: a(3), r(3)
  checks = 0
  a = [payload(1), payload(2), payload(3)]
  r = eoshift(a, 1, payload(99))
  call require('EOSHIFT derived type ARRAY positive control', r(1)%tag == 2 .and. r(3)%tag == 99, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT DERIVED BOUNDARY CONTROL OK'
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
end program i169h_eoshift_derived_boundary_control
