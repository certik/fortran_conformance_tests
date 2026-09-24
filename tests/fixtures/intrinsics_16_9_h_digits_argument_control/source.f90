! rule: S16.9.71-003
! covers: digits-x-integer-or-real
program i169h_digits_argument_control
  implicit none
  integer :: checks
  integer :: ix(2)
  real :: rx(2)
  checks = 0
  ix = [1, 2]
  rx = [1.0, 2.0]
  call require('integer and real DIGITS arguments admitted', &
       digits(ix(1)) == digits(ix) .and. digits(rx(1)) == digits(rx), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DIGITS ARGUMENT CONTROL OK'
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
end program i169h_digits_argument_control
