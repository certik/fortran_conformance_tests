! rule: C902
! covers: nonpointer-result-excluded
! evidence: effect
! standard: f2023
! oracle-basis: standard
module dataobj_c902_nonpointer_m
contains
  function f() result(r)
    integer :: r
    r = 1
  end function
end module dataobj_c902_nonpointer_m
program dataobj_c902_nonpointer_result
  use dataobj_c902_nonpointer_m
  implicit none
  f() = 31
end program dataobj_c902_nonpointer_result
