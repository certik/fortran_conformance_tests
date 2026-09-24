! rule: S16.9.71-001
! covers: digits-significant-digits-description
program i169h_digits_description
  implicit none
  integer :: checks
  checks = 0
  call require('DIGITS observes numeric model significant digits', digits(1) > 0 .and. digits(1.0) > 1, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS DESCRIPTION OK'
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
end program i169h_digits_description
