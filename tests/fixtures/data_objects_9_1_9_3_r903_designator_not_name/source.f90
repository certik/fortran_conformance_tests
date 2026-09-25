! rule: R903
! covers: not-designator-syntax
! evidence: effect
! standard: f2023
! oracle-basis: standard
program dataobj_r903_designator_not_name
  implicit none
  integer :: x(2)
  namelist /grp/ x(1)
end program dataobj_r903_designator_not_name
