! rule: S16.9.77-004
! covers: EOSHIFT-default-boundary-character-blanks
program i169h_eoshift_default_boundary_character
  implicit none
  character(len=3) :: a(3), r(3), q(3)
  integer :: checks
  checks = 0
  a = [character(len=3) :: 'abc', 'def', 'ghi']
  r = eoshift(a, 1); q = eoshift(a, 1, 'xyz')
  call require('EOSHIFT-default-boundary-character-blanks', &
       len(eoshift(a, 1)) == 3 .and. r(3) == '   ' .and. q(3) == 'xyz', checks)
  if (checks /= 1) error stop
  write(*,'(a)') 'INTRINSICS 16.9 H EOSHIFT DEFAULT BOUNDARY CHARACTER OK'
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
end program i169h_eoshift_default_boundary_character
