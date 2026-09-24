! rule: S16.9.92-002
! covers: GET_COMMAND-command-assigned-entire-command-or-blanks
! covers: GET_COMMAND-length-significant-or-zero
! covers: GET_COMMAND-length-independent-of-command-buffer
program i169k_get_command_effects
  implicit none
  integer :: checks
  integer :: length_full, status_full, length_absent, status_absent
  integer :: length_short, status_short
  character(len=1024) :: command_full
  character(len=2) :: command_short
  checks = 0
  command_full = repeat('#', len(command_full)); length_full = -7777; status_full = -7777
  call get_command(command_full, length_full, status_full)
  call require('GET_COMMAND assigns command with bounded trimmed length and blank fill', &
       status_full == 0 .and. len_trim(command_full) <= length_full .and. &
       blank_after(command_full, length_full), checks)
  length_absent = -7777; status_absent = -7777
  call get_command(length=length_absent, status=status_absent)
  call require('GET_COMMAND reports significant length for successful retrieval', &
       status_absent == 0 .and. length_absent >= 0, checks)
  command_short = '##'; length_short = -7777; status_short = -7777
  call get_command(command_short, length_short, status_short)
  call require('GET_COMMAND LENGTH ignores COMMAND buffer truncation', &
       status_short == -1 .and. length_short == length_absent, checks)
  if (checks /= 3) error stop
  write(*,'(a)') 'INTRINSICS 16.9 K GET COMMAND EFFECTS OK'
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
end program i169k_get_command_effects
