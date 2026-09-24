! rule: S16.9.93-003
! covers: GET_COMMAND_ARGUMENT-positive-arguments-consecutive
program i169k_command_argument_numbering
  implicit none
  integer :: checks
  integer :: n, status_first, status_after
  character(len=8) :: first, after
  checks = 0
  n = command_argument_count()
  first = '########'; status_first = -7777
  call get_command_argument(1, value=first, status=status_first)
  after = '########'; status_after = -7777
  call get_command_argument(n + 1, value=after, status=status_after)
  call require('positive command arguments are consecutive from one through count', &
       n == 1 .and. status_first == 0 .and. first(1:5) == 'omega' .and. &
       status_after > 0 .and. all_blank(after), checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K COMMAND ARGUMENT NUMBERING OK'
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
end program i169k_command_argument_numbering
