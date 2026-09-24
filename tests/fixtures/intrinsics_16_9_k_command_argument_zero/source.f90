! rule: S16.9.93-002
! covers: GET_COMMAND_ARGUMENT-zero-always-exists
program i169k_command_argument_zero
  implicit none
  integer :: checks
  integer :: n, length_zero, status_zero
  checks = 0
  n = command_argument_count()
  length_zero = -7777; status_zero = -7777
  call get_command_argument(0, length=length_zero, status=status_zero)
  call require('command argument zero exists without spelling oracle', &
       status_zero == 0 .and. length_zero >= 0, checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K COMMAND ARGUMENT ZERO OK'
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
end program i169k_command_argument_zero
