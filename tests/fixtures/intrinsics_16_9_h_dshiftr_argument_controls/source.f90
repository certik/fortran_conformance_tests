! rule: S16.9.76-001
! covers: DSHIFTR-I-integer-or-boz
! covers: DSHIFTR-J-integer-or-boz
program i169h_dshiftr_argument_controls
  implicit none
  integer :: checks
  integer :: i, j, n
  checks = 0
  n = bit_size(0)
  i = ior(shiftl(1, 0), shiftl(1, 2))
  j = shiftl(1, 2)
  call require('dshiftr integer and BOZ I admitted', &
       btest(dshiftr(i, j, 1), n - 1) .and. btest(dshiftr(z'03', j, 2), n - 1), checks)
  call require('dshiftr integer and BOZ J admitted', &
       btest(dshiftr(i, j, 1), 1) .and. btest(dshiftr(i, z'03', 1), 0), checks)
  if (checks /= 2) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H DSHIFTR ARGUMENT CONTROLS OK'
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
end program i169h_dshiftr_argument_controls
