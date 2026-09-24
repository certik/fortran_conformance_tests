! rule: S16.9.93-006
! covers: GET_COMMAND_ARGUMENT-status-positive-for-negative-number
! covers: GET_COMMAND_ARGUMENT-status-minus-one-for-value-truncation
! covers: GET_COMMAND_ARGUMENT-status-zero-for-nonfailure-nontruncation
program i169k_command_argument_status
  implicit none
  integer :: checks
  integer :: status_negative, length_long, status_long, length_short, status_short
  character(len=8) :: long_value
  character(len=2) :: short_value
  checks = 0
  status_negative = -7777
  call get_command_argument(-1, status=status_negative)
  call require('negative NUMBER gives positive STATUS', status_negative > 0, checks)
  long_value = '########'; length_long = -7777; status_long = -7777
  call get_command_argument(1, value=long_value, length=length_long, status=status_long)
  call require('nonfailure nontruncating argument has STATUS zero', &
       status_long == 0 .and. length_long == 5 .and. long_value(1:5) == 'omega', checks)
  short_value = '##'; length_short = -7777; status_short = -7777
  call get_command_argument(1, value=short_value, length=length_short, status=status_short)
  call require('short VALUE argument gives STATUS minus one', &
       status_short == -1 .and. length_short == 5 .and. short_value == 'om', checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K COMMAND ARGUMENT STATUS OK'
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

  logical function all_blank(text)
    character(len=*), intent(in) :: text
    integer :: i
    all_blank = .true.
    do i = 1, len(text)
      if (text(i:i) /= ' ') all_blank = .false.
    end do
  end function all_blank

  logical function blank_after(text, used)
    character(len=*), intent(in) :: text
    integer, intent(in) :: used
    if (used < 0) then
      blank_after = .false.
    else if (used >= len(text)) then
      blank_after = .true.
    else
      blank_after = all_blank(text(used + 1:))
    end if
  end function blank_after
end program i169k_command_argument_status
