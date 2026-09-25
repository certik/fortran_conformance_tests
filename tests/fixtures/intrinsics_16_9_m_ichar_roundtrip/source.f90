! rule: S16.9.105-003
! covers: ICHAR-CHAR-index-round-trip-guaranteed-range
program i169m_ichar_roundtrip
  implicit none
  integer :: checks
  checks = 0
  call require('ICHAR CHAR index round trip for guaranteed range', &
       ichar(char(0)) == 0 .and. ichar(char(32)) == 32 .and. ichar(char(65)) == 65, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 M ICHAR ROUNDTRIP OK'
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
end program i169m_ichar_roundtrip
