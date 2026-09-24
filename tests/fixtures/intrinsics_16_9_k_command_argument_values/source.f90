! rule: S16.9.93-004
! covers: GET_COMMAND_ARGUMENT-absent-value-all-blanks
! covers: GET_COMMAND_ARGUMENT-absent-length-zero
! covers: GET_COMMAND_ARGUMENT-length-independent-of-value-buffer
! covers: GET_COMMAND_ARGUMENT-existing-value-processor-supplied
program i169k_command_argument_values
  implicit none
  integer :: checks
  integer :: n, length_absent, length_no_value, length_with_value
  character(len=8) :: absent_value, existing_value, short_absent
  checks = 0
  n = command_argument_count()
  absent_value = '########'
  call get_command_argument(n + 1, value=absent_value)
  call require('absent command argument assigns VALUE blanks', all_blank(absent_value), checks)
  length_absent = -7777
  call get_command_argument(n + 1, length=length_absent)
  call require('absent command argument assigns LENGTH zero', length_absent == 0, checks)
  length_no_value = -7777; length_with_value = -8888; short_absent = '########'
  call get_command_argument(n + 1, length=length_no_value)
  call get_command_argument(n + 1, value=short_absent, length=length_with_value)
  call require('absent LENGTH ignores VALUE buffer size', &
       length_no_value == 0 .and. length_with_value == 0 .and. all_blank(short_absent), checks)
  existing_value = '########'
  call get_command_argument(1, value=existing_value)
  call require('sole supplied command argument value is observed', &
       existing_value(1:5) == 'omega' .and. all_blank(existing_value(6:)), checks)
  if (checks /= 4) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K COMMAND ARGUMENT VALUES OK'
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
end program i169k_command_argument_values
