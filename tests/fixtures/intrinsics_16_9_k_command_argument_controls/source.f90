! rule: S16.9.93-001
! covers: GET_COMMAND_ARGUMENT-NUMBER-integer-scalar
! covers: GET_COMMAND_ARGUMENT-VALUE-default-character-scalar
! covers: GET_COMMAND_ARGUMENT-LENGTH-integer-scalar-range
! covers: GET_COMMAND_ARGUMENT-STATUS-integer-scalar-range
! covers: GET_COMMAND_ARGUMENT-argument-intents
program i169k_command_argument_controls
  implicit none
  integer :: checks
  integer :: n, length_number, length_only, status_number, status_only
  character(len=8) :: value_number, value_only, value_intent
  integer :: length_intent, status_intent
  checks = 0
  n = command_argument_count()
  value_number = '########'; length_number = -7777; status_number = -7777
  call get_command_argument(1, value_number, length_number, status_number)
  call require('NUMBER integer scalar actual selects supplied argument', &
       status_number == 0 .and. length_number == 5 .and. value_number(1:5) == 'omega', checks)
  value_only = '########'
  call get_command_argument(1, value_only)
  call require('VALUE default character scalar actual is assigned', &
       value_only(1:5) == 'omega' .and. all_blank(value_only(6:)), checks)
  length_only = -7777
  call get_command_argument(1, length=length_only)
  call require('LENGTH integer scalar actual is assigned', length_only == 5, checks)
  status_only = -7777
  call get_command_argument(1, status=status_only)
  call require('STATUS integer scalar actual is assigned', status_only == 0, checks)
  value_intent = '########'; length_intent = -7777; status_intent = -7777
  call get_command_argument(1, value_intent, length_intent, status_intent)
  call require('OUT arguments are defined by GET_COMMAND_ARGUMENT', &
       value_intent(1:5) == 'omega' .and. length_intent == 5 .and. status_intent == 0, checks)
  if (checks /= 5) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K COMMAND ARGUMENT CONTROLS OK'
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
end program i169k_command_argument_controls
