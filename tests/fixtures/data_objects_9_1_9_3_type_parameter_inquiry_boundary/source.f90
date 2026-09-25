! rule: R902
! covers: type-parameter-inquiry-boundary
! evidence: effect
! standard: f2023
! oracle-basis: standard
program dataobj_type_parameter_inquiry_boundary
  implicit none
  character(len=3) :: c
  c%len = 4
end program dataobj_type_parameter_inquiry_boundary
