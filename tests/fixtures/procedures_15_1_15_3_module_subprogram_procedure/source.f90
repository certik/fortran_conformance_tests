! rule: S15.2.2.2-006
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module module_subprogram_procedure_m
  implicit none
contains
  integer function answer()
    answer = 42
  end function
  integer function wrong_answer()
    wrong_answer = -999
  end function
end module
program module_subprogram_procedure
  use module_subprogram_procedure_m
  implicit none
  integer :: result
  result = -777
  result = answer()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.2 MODULE PROCEDURE OK'
end program
