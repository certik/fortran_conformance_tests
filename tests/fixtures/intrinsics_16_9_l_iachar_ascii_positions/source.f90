! rule: S16.9.98-003
! covers: IACHAR-ASCII-position-exact
! covers: IACHAR-ASCII-result-range
program i169l_iachar_ascii_positions
  implicit none
  interface type_code
    procedure type_code_integer, type_code_real
  end interface
  integer :: checks
  checks = 0
  call require('IACHAR ASCII positions are exact', &
       iachar(' ') == 32 .and. iachar('0') == 48 .and. &
       iachar('A') == 65 .and. iachar('X') == 88, checks)
  call require('IACHAR ASCII positions are in range', &
       all([iachar(' '), iachar('0'), iachar('A'), iachar('X')] >= 0) .and. &
       all([iachar(' '), iachar('0'), iachar('A'), iachar('X')] <= 127), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 L IACHAR ASCII POSITIONS OK'
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
  integer function type_code_integer(x)
    integer, intent(in) :: x
    type_code_integer = 1
  end function type_code_integer
  integer function type_code_real(x)
    real, intent(in) :: x
    type_code_real = 2
  end function type_code_real
end program i169l_iachar_ascii_positions
