! rule: S16.9.75-001
! covers: DSHIFTL-I-integer-or-boz
! covers: DSHIFTL-J-integer-or-boz
program i169h_dshiftl_argument_controls
  implicit none
  integer :: checks
  integer :: i, j, n
  checks = 0
  n = bit_size(0)
  i = ior(shiftl(1, 0), shiftl(1, 2))
  j = ior(shiftl(1, n - 1), shiftl(1, n - 3))
  call require('dshiftl integer and BOZ I admitted', &
       btest(dshiftl(i, j, 1), 1) .and. btest(dshiftl(z'03', j, 1), 2), checks)
  call require('dshiftl integer and BOZ J admitted', &
       btest(dshiftl(i, j, 1), 1) .and. btest(dshiftl(i, z'03', n - 1), 0), checks)
  if (dshiftl(i, j, 0) == dshiftl(i, j, n)) then
    write(*,'(a)') 'dshiftl full-width edge differs from zero shift'
    error stop
  end if
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTL ARGUMENT CONTROLS OK'
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
end program i169h_dshiftl_argument_controls
