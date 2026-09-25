! rule: S16.9.105-005
! covers: ICHAR-order-consistent-with-character-le
! covers: ICHAR-equality-consistent-with-character-equality
program i169m_ichar_order_equality
  implicit none
  character(len=1) :: c10, c11, c12, c13
  integer :: checks
  checks = 0
  c10 = char(10)
  c11 = char(11)
  c12 = char(12)
  c13 = char(13)
  call require('ICHAR order agrees with character comparison', c10 <= c11 .and. ichar(c10) <= ichar(c11), checks)
  call require('ICHAR equality agrees with character equality', &
       c12 == char(12) .and. ichar(c12) == ichar(char(12)) .and. c12 /= c13 .and. ichar(c12) /= ichar(c13), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M ICHAR ORDER EQUALITY OK'
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
end program i169m_ichar_order_equality
