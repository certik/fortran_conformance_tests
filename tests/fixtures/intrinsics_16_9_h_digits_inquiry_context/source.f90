! rule: S16.9.71-002
! covers: digits-inquiry-class
program i169h_digits_inquiry_context
  implicit none
  integer, parameter :: q_from_initialization = digits(7)
  integer :: checks
  checks = 0
  call require('DIGITS is usable as inquiry initialization', q_from_initialization == digits(9), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS INQUIRY CONTEXT OK'
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
end program i169h_digits_inquiry_context
