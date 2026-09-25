! rule: S7.5.10-003
! covers: character-length-conversion, no-defined-assignment-during-construction
! Oracles hand-derived from Fortran 2023 7.5.10 p1-p8/C7106/C7108.
module sc_b_assignment_mod
implicit none
integer :: calls = 0
type :: chars
  character(len=5) :: wide
  character(len=2) :: narrow
end type chars
type :: inner
  integer :: value
contains
  procedure :: assign_inner
  generic :: assignment(=) => assign_inner
end type inner
type :: outer
  type(inner) :: item
end type outer
contains
subroutine assign_inner(lhs, rhs)
  class(inner), intent(out) :: lhs
  type(inner), intent(in) :: rhs
  calls = calls + 1
  lhs%value = rhs%value + 100
end subroutine assign_inner
subroutine observe_chars(x)
  type(chars), intent(in) :: x
  if (len(x%wide) /= 5) error stop 1
  if (x%wide /= 'AB   ') error stop 2
  if (len(x%narrow) /= 2) error stop 3
  if (x%narrow /= 'WX') error stop 4
end subroutine observe_chars
subroutine observe_outer(x)
  type(outer), intent(in) :: x
  if (x%item%value /= 17) error stop 5
  if (calls /= 0) error stop 6
end subroutine observe_outer
end module sc_b_assignment_mod
program structure_constructor_7_5_10_b_character_assignment
use sc_b_assignment_mod
implicit none
character(len=2) :: short
character(len=4) :: long
character(len=1) :: sentinel
type(inner) :: src
type(outer) :: scratch
sentinel = '#'
short = 'AB'
long = 'WXYZ'
src%value = 17
calls = 0
call observe_chars(chars(short, long))
call observe_outer(outer(src))
if (sentinel /= '#') error stop 7
write(*,'(a)') 'STRUCTURE CONSTRUCTOR CHARACTER AND DEFINED ASSIGNMENT OK'
end program structure_constructor_7_5_10_b_character_assignment
