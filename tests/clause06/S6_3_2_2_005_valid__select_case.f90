! rule: S6.3.2.2-005
! covers: select-case end-select
! evidence: positive-control
program select_case_spellings
  implicit none
  integer :: value
  value = 0
  selectcase(1)
  case(1)
    value = 7
  case default
    stop 1
  endselect
  if (value /= 7) stop 2
  select case(2)
  case(2)
    value = 9
  case default
    stop 3
  end select
  if (value /= 9) stop 4
end program
