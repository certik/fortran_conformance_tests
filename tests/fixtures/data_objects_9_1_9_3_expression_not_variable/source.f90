! rule: R902
! covers: expression-not-variable
! evidence: effect
! standard: f2023
! oracle-basis: standard
program dataobj_expression_not_variable
  implicit none
  integer :: x
  (x + 0) = 7
end program dataobj_expression_not_variable
