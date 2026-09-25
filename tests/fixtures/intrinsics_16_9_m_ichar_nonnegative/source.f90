! rule: S16.9.105-004
! covers: ICHAR-result-nonnegative
program i169m_ichar_nonnegative
  implicit none
  integer :: checks
  checks = 0
  call require('ICHAR result is nonnegative for representable character', &
       ichar(char(1)) > 0 .and. ichar('A') >= 0 .and. ichar('0') >= 0 .and. ichar(' ') >= 0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M ICHAR NONNEGATIVE OK'
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
end program i169m_ichar_nonnegative
