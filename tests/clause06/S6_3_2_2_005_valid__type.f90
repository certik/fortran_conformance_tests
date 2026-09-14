! rule: S6.3.2.2-005
! covers: end-type
! evidence: positive-control
program type_spellings
  implicit none
  type :: first_type
    integer :: value
  endtype first_type
  type :: second_type
    integer :: value
  end type second_type
  type(first_type) :: first
  type(second_type) :: second
  first%value = 7
  second%value = 9
  if (first%value /= 7) stop 1
  if (second%value /= 9) stop 2
end program
