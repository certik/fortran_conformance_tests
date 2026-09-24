! rule: S15.2.2.4-001
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
module procedure_pointer_attribute_m
  implicit none
  abstract interface
    integer function int_fun()
    end function
  end interface
contains
  integer function answer()
    answer = 42
  end function
  integer function wrong_answer()
    wrong_answer = -999
  end function
end module
program procedure_pointer_attribute
  use procedure_pointer_attribute_m
  implicit none
  procedure(int_fun), pointer :: p
  integer :: result
  p => answer
  result = -8
  result = p()
  if (result /= 42) error stop 1
  print '(a)', 'PROCEDURES 15.2.2.4 PROCEDURE POINTER ATTRIBUTE OK'
end program
